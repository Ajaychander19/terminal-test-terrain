import os
import psutil

from time import sleep, time
from datetime import datetime, timedelta
import pause

from MeasurementsWriter import MeasurementsWriter
from SerialConnection import SerialConnection
from ATCommandSender import ATCommandSender

from gpiozero import LED
from gpiozero import Button

from typing import TextIO

measurements_started = False
shutdown_requested = False
gps_error = False
network_error = False


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


def log_memory_usage(log_file: TextIO):
    """
    Log current time and memory usage to `log_file`. Time is given as float in seconds since epoch,
    The memory usage is given in KB.

    The line is written in the format as in the example below:
    1719909817.8414948,13502

    :param log_file: file access open in write mode when the log line will be written
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    log_file.write(f"{time()},{memory_info.rss / 1024}\n")


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


def check_for_sim(atcs: ATCommandSender, pin_code: str = "0000", log_file: TextIO = None) -> bool:
    """
    Checks if the SIM card is activated, if it isn't tries to unlock using `_pin_code` in a loop until it is activated
    or shutdown/measurements end was requested.

    The function tries to unlock the SIM card every 10 seconds and checks for its readiness every second because
    it cas take some time before the SIM card is activated after the PIN code has been sent.

    On average, this function takes 3 to 13 seconds to finish on start up and is nearly instant if the SIM card has
    already been activated

    :param log_file: file access open in write mode for memory logging
    :param pin_code: the pin code of the SIM card inserted in the module. Must be a numeric string in XXXX format.
    :param atcs: An instance of an initialized `ATCommandSender`
    :return: True when the SIM card is ready, False if the check was stopped externally
        (by requesting shutdown or measurements end by holding/pressing the push button)
    """
    global measurements_started
    global shutdown_requested

    before = datetime.now()
    cpt = 10  # try to unlock sim every 10 iterations of the loop
    sim_ready = "READY" in atcs.send_command("AT+CPIN?")
    while not sim_ready:
        if shutdown_requested or not measurements_started:
            return False

        if cpt == 10:
            print("SIM not ready, trying to unlock...")
            atcs.enter_pin(pin_code)
            cpt = 0

        sleep(1)
        cpt += 1
        sim_ready = "READY" in atcs.send_command("AT+CPIN?")

    print("SIM card ready")

    after = datetime.now()
    if (after - before).total_seconds() > 1.0:
        print("It took " + str((after - before).total_seconds())
              + " seconds to unlock the SIM")

    if log_file is not None:
        log_memory_usage(log_file)

    return True


def check_for_network(atcs: ATCommandSender, log_file: TextIO = None) -> bool:
    """
    Checks for network signal, looping until it is found or shutdown/measurements end was requested.

    In most cases it is instant, but sometimes it can last for 3-10 seconds on start up. Will loop infinitely if no
    network can be found for example when the SIM card is not activated or the module is forced in a network mode
    not available locally (for example when forced to 5G when no 5G cells are present)

    :param log_file: file access open in write mode for memory logging
    :param atcs: An instance of an initialized ATCommandSender
    :return: True when the network signal has been received, False if the check was stopped externally
        (by requesting shutdown or measurements end by holding/pressing the push button)
    """
    global measurements_started
    global shutdown_requested

    before = datetime.now()
    network_ok = "NO SERVICE" not in atcs.send_command('AT+CPSI?')
    if not network_ok:
        print("No service, waiting...")
    while not network_ok:
        if shutdown_requested or not measurements_started:
            return False

        sleep(1)  # CPSI is easy enough to do every second
        network_ok = "NO SERVICE" not in atcs.send_command('AT+CPSI?')

    print("Service OK")
    after = datetime.now()
    if (after - before).total_seconds() > 1.0:
        print("It took " + str((after - before).total_seconds())
              + " seconds to get network signal")

    if log_file is not None:
        log_memory_usage(log_file)

    return True


def check_for_gps(atcs: ATCommandSender, log_file: TextIO = None) -> bool:
    """
    Checks for GPS in a loop until a position is found or shutdown/measurements end was requested.

    This function can take anywhere from nearly instant (if a GPS fix is already acquired) to 3-4 minutes on average
    on start up of the module or even 10-15 minutes in the worst case (when the module has never got a GPS fix before)

    :param log_file: file access open in write mode for memory logging
    :param atcs: An instance of an initialized ATCommandSender
    :return: True when the GPS signal has been received, False if the check was stopped externally
        (by requesting shutdown or measurements end by holding/pressing the push button)
    """

    global measurements_started
    global shutdown_requested

    gps_signal_acquired = False
    before = datetime.now()
    while not gps_signal_acquired:
        if shutdown_requested or not measurements_started:
            return False

        print("Trying to acquire GPS signal...")
        # response = atcs.send_command('AT+CGPSINFO')
        # gps_signal_acquired = response.splitlines()[0].strip() != "+CGPSINFO: ,,,,,,,,"
        gps_signal_acquired = (atcs.get_gps_info() != "+CGPSINFO: ,,,,,,,,")
        sleep(1)

    print("GPS OK")

    after = datetime.now()
    if (after - before).total_seconds() > 1.0:
        print("It took " + str((after - before).total_seconds())
              + " seconds to get GPS signal")

    if log_file is not None:
        log_memory_usage(log_file)

    return True


def setup_module(atcs: ATCommandSender, log_file: TextIO = None):
    """
    Setups the module activating the SIM card, setting the network mode (LTE only by default), waiting for network
    and GPS signal.

    This function also controls the LEDs, so it must only be called in the scope where the LEDs are initialized
    (for example within the "with" block).

    :param atcs: An instance of an initialized ATCommandSender
    :param log_file: file access open in write mode for memory logging. If None, no logging will be done
    :return: Doesn't return any value but can return before it's finished if shutdown/measurements end was requested
    """
    global measurements_started
    global shutdown_requested

    init_start_time = datetime.now()

    red_led.blink(on_time=1, off_time=1)
    if not check_for_sim(atcs, "0000", log_file):
        return
    red_led.off()

    print("Defaulting to LTE only mode")
    atcs.send_command('AT+CNMP=38')

    red_led.blink(on_time=1, off_time=0.5)
    if not check_for_network(atcs, log_file):
        return
    red_led.off()

    # atcs.restart_gps()
    #
    # red_led.blink(on_time=0.5, off_time=3)
    # if not check_for_gps(atcs, log_file):
    #     return
    # red_led.off()

    print("It took " + str((datetime.now() - init_start_time).total_seconds())
          + " seconds to initialize")


def start_measurement_session():
    """
    Starts a new measurement session. This function opens a serial connection and sets up the module.
    It creates a new measurements file and loops forever, writing network and GPS data to the measurement file.

    The function powers down the module and returns as soon as possible when shutdown was requested.
    It also returns when measurement session end was requested either by pressing the button
    or by touching the stop file

    This function also controls the LEDs, so it must only be called in the scope where the LEDs are initialized
    (for example within the "with" block).

    :return: Doesn't return any value but can return before measurements start
        if shutdown/measurements end was requested
    """
    # TODO: Try to refactor the code
    global shutdown_requested
    global measurements_started
    global network_error
    global gps_error

    hour = datetime.now().strftime("%H-%M")
    log_file_path = f"./logs/{hour}_memory_usage.csv"
    green_led.off()
    red_led.on()
    # red led will be continuously on until the connection is established
    # usually it's instant, but sometimes it can take a while if program starts right at boot or if it's restarted
    with SerialConnection(module_path) as connection, open(log_file_path, "w") as log_file:
        log_file.write("timestamp,memory_usage_mb\n")
        atcs = ATCommandSender(connection)

        red_led.off()
        setup_module(atcs, log_file)
        if shutdown_requested:
            atcs.send_command("AT+CPOF")
            return
        if not measurements_started:
            return

        print("Starting measurements")
        green_led.on()
        file_path: str
        # I don't like storing the entire file content in memory
        # (even if it shouldn't be more than 100MB in the worst case)
        # but it seems to be the only way to reliably have it when rewriting the header
        file_content: list[str]
        with MeasurementsWriter(is_tmp=True, operator_info=atcs.get_operator()) as writer:
            file_path = writer.get_file_path()
            writer.print_header()

            # Wait until the start of the second to get a nice round number
            starting_time = datetime.now()
            starting_time = starting_time + timedelta(microseconds=(1000000 - starting_time.microsecond))
            pause.until(starting_time)

            file_time = None
            try:
                file_time = os.stat("./stop").st_ctime
            except OSError:
                print("WARNING: stop file not found, measurements will have to be stopped with the button")

            log_counter = 0
            current_measurement = 0
            continuous_gps_error_counter = 0
            gps_lost = False
            gps_error = network_error = current_gps_error = current_network_error = False
            last_error_state = (current_gps_error, current_network_error)
            print("Measurements loop started")
            while measurements_started and not shutdown_requested:
                green_led.on()

                for info in atcs.get_position(starting_time):  # TODO: There really is no need for a loop here
                    if not info:  # If no position found
                        current_gps_error = True
                        continuous_gps_error_counter += 1
                    else:
                        current_gps_error = False
                        continuous_gps_error_counter = 0
                    writer.print_gps_measurement(info)
                if continuous_gps_error_counter > 30:
                    print("No GPS signal for 30 seconds")
                    gps_lost = True
                    continuous_gps_error_counter = 0

                # Not sure if in NSA 5G both should be written or only one.
                for cell in atcs.get_serving_cell(starting_time):
                    if not cell:  # If no network found
                        current_network_error = True
                    else:
                        current_network_error = False
                    writer.print_serving_cell_measurement(cell)

                if not current_network_error:  # Only search for neighbours if serving cell is ok
                    for cell in atcs.get_neighbour_cells(starting_time):
                        writer.print_neighbour_cell_measurement(cell)

                # Check if error state has changed to prevent resetting error blink
                current_error_state = (current_gps_error, current_network_error)
                if current_error_state != last_error_state:
                    gps_error = current_gps_error
                    network_error = current_network_error
                    update_error_led()
                    last_error_state = current_error_state

                print("Measurement ", str(current_measurement),
                      " took ", (datetime.now() - starting_time).microseconds / 1000, " milliseconds")

                starting_time = datetime.now()
                starting_time = starting_time + timedelta(microseconds=(1000000 - starting_time.microsecond))
                green_led.off()
                pause.until(starting_time)

                if log_counter >= 30:  # Save memory readings every 30 measurements
                    log_memory_usage(log_file)
                    log_counter = 0
                log_counter += 1

                current_measurement += 1
                if file_time is not None:
                    # If the stop file was modified (by touch or else), stop the execution
                    if os.stat("./stop").st_ctime != file_time:
                        measurements_started = False
                        print("Measurements stopped via stop file")

            file_content = writer.file_content.splitlines(keepends=True)

        before = datetime.now()
        # Add the GPS lost header. This will rewrite the file, so it might take a bit of time
        MeasurementsWriter.add_gps_lost_header(file_path, gps_lost)
        print(f"It took {(datetime.now() - before).total_seconds()} seconds to add the GPS lost entry to the header")

        # Power down the module
        if shutdown_requested:
            atcs.send_command("AT+CPOF")
        green_led.off()
        red_led.off()


if __name__ == '__main__':
    dt_start = datetime.now()
    module_path = '/dev/ttyUSB2'

    with (LED("GPIO26") as green_led,
          LED("GPIO24") as red_led,
          Button("GPIO25", pull_up=True, bounce_time=0.1, hold_time=2) as start_button
          ):
        start_button.when_held = request_shutdown
        start_button.when_released = toggle_measurement_session

        # red led continuously
        red_led.on()
        # Check if the module is connected by checking the device file
        # Red will be lit on boot until the module is properly connected
        print("Waiting for module")
        while not os.path.exists(module_path):
            sleep(0.5)
            if shutdown_requested:
                green_led.close()
                red_led.close()
                start_button.close()
                print("Shutting down now")
                os.system("sudo shutdown -h now")
        print("Module found")

        # Waiting for at least 30 seconds is very important because after it is connected, the module sends a bunch
        # of messages to initialize. There is no way to know for sure when it's ended and writing/reading
        # during this time can create an infinite loop completely blocking the execution.
        print("Waiting 30 seconds at first boot to let module finish initializations...")
        for i in range(30):
            sleep(1)
            if shutdown_requested:
                green_led.close()
                red_led.close()
                start_button.close()
                print("Shutting down now")
                os.system("sudo shutdown -h now")

        red_led.off()

        green_led.on()
        print("Press start button to start measurements")
        while not shutdown_requested:
            if measurements_started:
                start_measurement_session()
                if not shutdown_requested:
                    print("Press start button to start a new measurements")
                    green_led.on()
            sleep(0.5)  # Maybe increase it, it kinda uses a lot of CPU time with 0.5 (>3%)

    # When shutdown is requested, wait the measurement session to end, reach end of context (close leds and buttons)
    # and shutdown
    print("Shutting down now")
    os.system("sudo shutdown -h now")
