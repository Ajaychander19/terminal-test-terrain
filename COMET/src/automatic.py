#!/usr/bin/python
import argparse
import logging
import os
import sys

import psutil

from time import sleep
from datetime import datetime, timedelta
import pause

from CometToCevConverter import CometToCevConverter
from MeasurementsWriter import MeasurementsWriter
from SerialConnection import SerialConnection
from ATCommandSender import ATCommandSender

from gpiozero import LED
from gpiozero import Button
from gpiozero import CPUTemperature

from typing import TextIO

measurements_started = False
shutdown_requested = False
gps_error = False
network_error = False
pin_code = ""  # Must be set from argument with set_pin_from_args function


def set_pin_from_args():
    """
    Parse the command line arguments for pin code and set the global `pin_code` variable.

    If given in wrong format (not numeric and 4 character long), blink red until a shutdown is requested.
    """
    global pin_code
    parser = argparse.ArgumentParser("python automatic.py")
    parser.add_argument("pin", help="A 4 number long pin code. 0000 if not given", type=str)
    args = parser.parse_args()

    if not args.pin or not args.pin.strip().isnumeric() or not len(args.pin.strip()) == 4:
        logger.critical(f"Incorrect PIN code was given: '{args.pin}'. Must be 4 numeric characters long. "
                        f"The program will not continue.")
        red_led.blink(on_time=1, off_time=1)
        while True:
            sleep(0.5)
            if shutdown_requested:
                return

    pin_code = args.pin.strip()


def setup_comet_logger(print_to_stdout: bool = False):
    """
    Set up and return the "COMET" logger.

    :param print_to_stdout: If True, all logged messages will be printed to the terminal as well
    :return: Set up logger
    """
    log_dir_path = os.path.abspath(f'./logs/{datetime.now().strftime("%Y-%m-%d")}')
    if not os.path.isdir(log_dir_path):
        os.makedirs(log_dir_path)

    # Must be named COMET so that other modules could access it without passing the instance
    res = logging.getLogger("COMET")

    formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
    handler = logging.FileHandler(f'{log_dir_path}/comet_{datetime.now().strftime("%Y-%m-%d")}.log')
    handler.setFormatter(formatter)

    res.setLevel(logging.DEBUG)
    res.addHandler(handler)

    if print_to_stdout:
        res.addHandler(logging.StreamHandler(sys.stdout))  # print the messages to console too
    return res


def toggle_measurement_session():
    """
    Toggle the global variable `measurements_started` indicating if a measurement session must start or stop
    """
    global measurements_started
    measurements_started = not measurements_started


def request_shutdown():
    """
    Set the global variable `shutdown_requested` to True indicating that a graceful shutdown must occur
    as soon as possible
    """
    global shutdown_requested
    shutdown_requested = True


def log_temperature_error():
    """Prints a critical error if the temperature exceeded 80 degrees"""
    logger.critical("CPU temperature exceeded 80 degrees Celsius! ")


def log_system_metrics(log_file: TextIO):
    """
    Log current time and memory usage to `log_file`. Time is given as float in seconds since epoch,
    The memory usage is given in KB, the temperature is given in degrees Celsius.

    The line is written in the following format:
    time_in_epoch,memory_in_KB,process_memory_consumption_percent,total_memory_consumption_percent,cpu_use_percent,
    cpu_temperature_in_degrees

    :param log_file: file access open in write mode when the log line will be written
    """
    process = psutil.Process(os.getpid())
    log_file.write(f"{str(datetime.now())},{process.memory_info().rss / 1024},{process.memory_percent()},"
                   f"{psutil.virtual_memory().percent},{psutil.cpu_percent()},{cpu.temperature}\n")


def update_error_led():
    """
    Updates the blinking rate of the red error LED depending on the current error status
    (global variables `gps_error` and `network_error`).

    `LED codes`
     - 500ms on, 500ms off when both `gps_error` and `network_error` are True
     - 500ms on, 3000ms off when only `gps_error` is True
     - 3000 on, 500ms off when only `network_error` is True
     - Always off when both `gps_error` and `network_error` are False
    """
    global gps_error
    global network_error
    if gps_error and network_error:
        # Both errors present, use the fastest blink pattern
        red_led.off()
        red_led.blink(on_time=0.5, off_time=0.5)
    elif gps_error:
        # Only GPS error
        red_led.off()
        red_led.blink(on_time=0.5, off_time=3)
    elif network_error:
        # Only network error
        red_led.off()
        red_led.blink(on_time=3, off_time=0.5)
    else:
        # No errors
        red_led.off()


def check_for_sim(atcs: ATCommandSender) -> bool:
    """
    Checks if the SIM card is activated, if it isn't tries to unlock using the global variable`pin_code`
    in a loop until it is activated or shutdown/measurements end was requested.

    The function tries to unlock the SIM card every 10 seconds and checks for its readiness every second because
    it cas take some time before the SIM card is activated after the PIN code has been sent.

    On average, this function takes 3 to 13 seconds to finish on start up and is nearly instant if the SIM card has
    already been activated

    :param atcs: An instance of an initialized `ATCommandSender`
    :return: True when the SIM card is ready, False if the check was stopped externally
        (by requesting shutdown or measurements end by holding/pressing the push button)
    """
    global measurements_started
    global shutdown_requested
    global pin_code

    before = datetime.now()
    cpt = 10  # try to unlock sim every 10 iterations of the loop
    sim_ready = "READY" in atcs.send_command("AT+CPIN?", logger)
    while not sim_ready:
        nb_left = atcs.get_pin_times()
        if nb_left < 3:
            logger.critical(f"Only {nb_left} times remain to input the PIN code meaning that the PIN code used "
                            f"({pin_code}) is likely wrong. The program will not continue. Please correct the "
                            f"PIN code in the 'comet.sh' script and unlock the SIM card manually using the interactive"
                            f"version of the software.)")
            while True:  # Wait until shutdown continuing blinking
                sleep(0.5)
                if shutdown_requested:
                    return False

        if shutdown_requested or not measurements_started:
            return False

        if cpt == 10:
            logger.info("SIM not ready, trying to unlock...")
            # TODO: Check if it really can be necessary to do it more than once if the pin is good
            atcs.enter_pin(pin_code, logger)
            cpt = 0

        sleep(1)
        cpt += 1
        sim_ready = "READY" in atcs.send_command("AT+CPIN?", logger)

    logger.info("SIM card ready")

    after = datetime.now()
    if (after - before).total_seconds() > 1.0:
        logger.debug(f"It took {str((after - before).total_seconds())} seconds to unlock the SIM")

    return True


def check_for_network(atcs: ATCommandSender) -> bool:
    """
    Checks for network signal, looping until it is found or shutdown/measurements end was requested.

    In most cases it is instant, but sometimes it can last for 3-10 seconds on start up. Will loop infinitely if no
    network can be found for example when the SIM card is not activated or the module is forced in a network mode
    not available locally (for example when forced to 5G when no 5G cells are present)

    :param atcs: An instance of an initialized ATCommandSender
    :return: True when the network signal has been received, False if the check was stopped externally
        (by requesting shutdown or measurements end by holding/pressing the push button)
    """
    global measurements_started
    global shutdown_requested

    before = datetime.now()
    network_ok = "NO SERVICE" not in atcs.send_command('AT+CPSI?', logger)
    if not network_ok:
        logger.info("No service, waiting...")
    while not network_ok:
        if shutdown_requested or not measurements_started:
            return False

        sleep(1)  # CPSI is easy enough to do every second
        network_ok = "NO SERVICE" not in atcs.send_command('AT+CPSI?', logger)

    logger.info("Service OK")
    after = datetime.now()
    if (after - before).total_seconds() > 1.0:
        logger.debug(f"It took {str((after - before).total_seconds())} seconds to get network signal")

    return True


def check_for_gps(atcs: ATCommandSender) -> bool:
    """
    Checks for GPS in a loop until a position is found or shutdown/measurements end was requested.

    This function can take anywhere from nearly instant (if a GPS fix is already acquired) to 3-4 minutes on average
    on start up of the module or even 10-15 minutes in the worst case (when the module has never got a GPS fix before)

    :param atcs: An instance of an initialized ATCommandSender
    :return: True when the GPS signal has been received, False if the check was stopped externally
        (by requesting shutdown or measurements end by holding/pressing the push button)
    """
    global measurements_started
    global shutdown_requested

    gps_signal_acquired = False
    before = datetime.now()
    log_counter = 60
    while not gps_signal_acquired:
        if shutdown_requested or not measurements_started:
            return False

        if log_counter >= 60:
            logger.info("Trying to acquire GPS signal...")
            log_counter = 0

        gps_signal_acquired = (atcs.get_gps_info() != "+CGPSINFO: ,,,,,,,,")
        log_counter += 1
        sleep(1)

    logger.info("GPS OK")

    after = datetime.now()
    if (after - before).total_seconds() > 1.0:
        logger.debug(f"It took {str((after - before).total_seconds())} seconds to get GPS signal")

    return True


def setup_module(atcs: ATCommandSender, metrics_log_file: TextIO = None):
    """
    Setups the module activating the SIM card, setting the network mode (LTE only by default), waiting for network
    and GPS signal.

    This function also controls the LEDs, so it must only be called in the scope where the LEDs are initialized
    (for example within the "with" block).

    :param atcs: An instance of an initialized ATCommandSender
    :param metrics_log_file: file access open in write mode for memory logging. If None, no logging will be done
    :return: Doesn't return any value but can return before it's finished if shutdown/measurements end was requested
    """
    global measurements_started
    global shutdown_requested

    setup_start_time = datetime.now()

    red_led.blink(on_time=1, off_time=1)
    if not check_for_sim(atcs):
        return
    red_led.off()

    logger.info("Defaulting to LTE only mode")
    atcs.send_command('AT+CNMP=38', logger)

    red_led.blink(on_time=3, off_time=0.5)
    if not check_for_network(atcs):
        return
    red_led.off()

    atcs.setup_gps(logger)
    red_led.blink(on_time=0.5, off_time=3)
    if not check_for_gps(atcs):
        return
    red_led.off()

    # Only write logs if the function didn't finish prematurely because of a shutdown/session end request
    if metrics_log_file is not None:
        log_system_metrics(metrics_log_file)
    logger.info(f"It took {str((datetime.now() - setup_start_time).total_seconds())} seconds to initialize")


# This function feels too long, but I'm not sure how to refactor it properly
def start_measurement_session():
    """
    Starts a new measurement session. This function opens a serial connection and sets up the module.
    It creates a new measurement file and loops forever, writing network and GPS data to the measurement file.

    The function powers down the module and returns as soon as possible when shutdown was requested.
    It also returns when measurement session end was requested either by pressing the button
    or by touching the stop file

    This function also controls the LEDs, so it must only be called in the scope where the LEDs are initialized
    (for example within the "with" block).

    :return: Doesn't return any value but can return before measurements start
        if shutdown/measurements end was requested
    """
    global shutdown_requested
    global measurements_started
    global network_error
    global gps_error

    logs_dir = f"./logs/{datetime.now().strftime('%Y-%m-%d')}/"
    metrics_log_filename = f"{logs_dir}{datetime.now().strftime('%H-%M')}_memory_usage.csv"
    if not os.path.isdir(logs_dir):
        os.makedirs(logs_dir)

    green_led.off()
    red_led.on()
    # red led will be continuously on until the connection is established
    # usually it's instant, but sometimes it can take a while if program starts right at boot or if it's restarted
    logger.info(f"Opening serial connection on {module_path}")
    before = datetime.now()
    # TODO: Use a logger for the system metrics log file
    with (SerialConnection(module_path, logger=logger) as connection,
          open(metrics_log_filename, "w", buffering=1) as metrics_log):
        logger.debug(f"Serial connection opened on {module_path}, took {(datetime.now() - before).total_seconds()}")
        logger.info("Starting a new measurement session")
        metrics_log.write("timestamp,process_memory_usage_kb,process_memory_usage_percent,"
                          "total_memory_usage_percent,total_cpu_percent,cpu_temperature\n")
        log_system_metrics(metrics_log)
        atcs = ATCommandSender(connection)

        red_led.off()
        setup_module(atcs, metrics_log)
        if shutdown_requested:
            logger.info("Powering down the module")
            atcs.send_command("AT+CPOF", logger)
            return
        if not measurements_started:
            return

        logger.info("Commencing measurements")
        green_led.on()
        file_path: str
        with MeasurementsWriter(operator_info=atcs.get_operator()) as writer:
            file_path = writer.get_file_path()
            writer.print_header()

            # Wait until the start of the second to get a nice round number
            starting_time = datetime.now()
            starting_time = starting_time + timedelta(microseconds=(1000000 - starting_time.microsecond))
            pause.until(starting_time)

            log_counter = 0
            current_measurement = 0
            continuous_gps_error_counter = 0
            gps_lost = False
            gps_error = network_error = current_gps_error = current_network_error = False
            last_error_state = (current_gps_error, current_network_error)
            logger.debug("Measurements loop started")
            while measurements_started and not shutdown_requested:
                green_led.on()

                gps_info = atcs.get_position(starting_time)
                if not gps_info:  # If no position found
                    current_gps_error = True
                    continuous_gps_error_counter += 1
                else:
                    current_gps_error = False
                    continuous_gps_error_counter = 0
                writer.print_gps_measurement(gps_info)
                if continuous_gps_error_counter > 30:
                    logger.warning("No GPS signal for 30 seconds")
                    gps_lost = True
                    continuous_gps_error_counter = 0

                # Not sure if in NSA 5G both should be written or only one.
                for cell in atcs.get_serving_cell(starting_time):
                    if not cell:  # If no network found
                        current_network_error = True
                    else:
                        current_network_error = False
                    writer.print_serving_cell_measurement(cell)

                # Only search for neighbours if serving cell is ok
                if not current_network_error:
                    for cell in atcs.get_neighbour_cells(starting_time):
                        writer.print_neighbour_cell_measurement(cell)

                # Check if error state has changed to prevent resetting error blink
                current_error_state = (current_gps_error, current_network_error)
                if current_error_state != last_error_state:
                    gps_error = current_gps_error
                    network_error = current_network_error
                    update_error_led()
                    last_error_state = current_error_state

                logger.info(f"Measurement {str(current_measurement)} took "
                            f"{(datetime.now() - starting_time).microseconds / 1000} milliseconds")

                starting_time = datetime.now()
                starting_time = starting_time + timedelta(microseconds=(1000000 - starting_time.microsecond))
                green_led.off()
                pause.until(starting_time)

                if log_counter >= 30:  # Save memory readings every 30 measurements
                    log_system_metrics(metrics_log)
                    log_counter = 0
                log_counter += 1

                current_measurement += 1

        # Add the GPS lost header. This will rewrite the file, so it might take a bit of time
        MeasurementsWriter.add_gps_lost_header(file_path, gps_lost)
        logger.debug("GPS_LOST header modified")

        # Once the measurement file is done, make a converted cev file from it
        green_led.off()
        green_led.blink(on_time=0.1, off_time=0.1)
        with CometToCevConverter(measurements_file_path=file_path, output_dir="./cev", logger=logger) as writer:
            writer.process()
        green_led.off()

        # Power down the module
        if shutdown_requested:
            logger.info("Powering down the module")
            atcs.send_command("AT+CPOF", logger)
        green_led.off()
        red_led.off()


def shutdown_with_leds():
    """
    Close the GPIO pins and shut down the computer
    """
    green_led.close()
    red_led.close()
    start_button.close()
    logger.info("Shutting down now\n\n")  # Empty line to separate different session on the same day
    os.system("sudo shutdown -h now")


if __name__ == '__main__':
    dt_start = datetime.now()
    module_path = '/dev/ttyUSB2'
    logger = setup_comet_logger(print_to_stdout=True)
    logger.info("Starting COMET")

    with (
        Button("GPIO17", pull_up=True, bounce_time=0.1, hold_time=2) as start_button,
        LED("GPIO16") as green_led,
        LED("GPIO26") as red_led,
        CPUTemperature(min_temp=20, max_temp=100) as cpu
    ):
        start_button.when_held = request_shutdown
        start_button.when_released = toggle_measurement_session
        cpu.when_activated = log_temperature_error

        # Doing this after getting LEDs to be able to blink red
        set_pin_from_args()
        if shutdown_requested:
            shutdown_with_leds()

        # red led continuously
        red_led.on()
        # Check if the module is connected by checking the device file
        # Red will be lit on boot until the module is properly connected
        logger.info("Waiting for module")
        while not os.path.exists(module_path):
            sleep(0.5)
            if shutdown_requested:
                shutdown_with_leds()
        logger.info("Module found")

        # Waiting for at least 30 seconds is very important because after it is connected, the module sends a bunch
        # of messages to initialize. There is no way to know for sure when it's ended and writing/reading
        # during this time can create an infinite loop completely blocking the execution.
        logger.info("Waiting 30 seconds at first boot to let module finish initializations...")
        for i in range(30):
            sleep(1)
            if shutdown_requested:
                shutdown_with_leds()

        red_led.off()

        green_led.on()
        logger.info("Waiting for the start button to be pushed")
        while not shutdown_requested:
            if measurements_started:
                start_measurement_session()
                logger.info("")  # Empty line to separate two measurements sessions
                red_led.off()
                if not shutdown_requested:
                    green_led.on()
            sleep(0.5)

    shutdown_with_leds()
