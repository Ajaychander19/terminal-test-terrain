import os
import time
from datetime import datetime, timedelta

import pause
import psutil

from FileWriters import MeasurementsWriter
from SerialConnection import SerialConnection
from ATCommandSender import ATCommandSender

from gpiozero import LED
from gpiozero import Button

measurements_started = False
shutdown_requested = False
gps_error = False
network_error = False


def start_measurements():
    global measurements_started
    measurements_started = not measurements_started


def shutdown():
    global shutdown_requested
    shutdown_requested = True


def log_memory_usage(log_file):
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    log_file.write(f"{time.time()},{memory_info.rss / 1024}\n")  # KB


def update_error_led():
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
        red_led.blink(on_time=1.0, off_time=0.5)
    else:
        # No errors
        red_led.off()


def init(atcs: ATCommandSender, log_file):
    global measurements_started
    global shutdown_requested

    print("Module initialisation started")
    sim_ready = "READY" in atcs.send_command("AT+CPIN?")

    if shutdown_requested or not measurements_started:
        return

    red_led.blink(on_time=1, off_time=1)
    cpt = 10  # try to unlock sim every 10 iterations of the loop
    before = datetime.now()
    while not sim_ready:
        if cpt == 10:
            print("SIM not ready, trying to unlock...")
            atcs.enter_pin("0000")
            cpt = 0

        time.sleep(1)
        cpt += 1
        sim_ready = "READY" in atcs.send_command("AT+CPIN?")

        if shutdown_requested or not measurements_started:
            return
    print("SIM card ready")
    after = datetime.now()
    if (after - before).total_seconds() > 1.0:
        print("It took " + str((after - before).total_seconds())
              + " seconds to unlock the SIM")

    red_led.off()

    log_memory_usage(log_file)

    print("Defaulting to LTE only mode")
    atcs.send_command('AT+CNMP=38')

    if shutdown_requested or not measurements_started:
        return

    red_led.blink(on_time=1, off_time=0.5)
    before = datetime.now()
    network_ok = "NO SERVICE" not in atcs.send_command('AT+CPSI?')
    if not network_ok:
        print("No service, waiting...")
    while not network_ok:
        time.sleep(1)  # CPSI is easy enough to do every second
        network_ok = "NO SERVICE" not in atcs.send_command('AT+CPSI?')

        if shutdown_requested or not measurements_started:
            return
    print("Service OK")
    after = datetime.now()
    if (after - before).total_seconds() > 1.0:
        print("It took " + str((after - before).total_seconds())
              + " seconds to get network signal")
    red_led.off()

    log_memory_usage(log_file)

    atcs.restart_gps()

    if shutdown_requested or not measurements_started:
        return

    # red_led.blink(on_time=0.5, off_time=3)
    # gps_signal_acquired = False
    # before = datetime.now()
    # while not gps_signal_acquired:
    #     print("Trying to acquire GPS signal...")
    #     # response = atcs.send_command('AT+CGPSINFO')
    #     # gps_signal_acquired = response.splitlines()[0].strip() != "+CGPSINFO: ,,,,,,,,"
    #     gps_signal_acquired = (atcs.get_gps_info() != "+CGPSINFO: ,,,,,,,,")
    #     time.sleep(1)
    #
    #     if shutdown_requested or not measurements_started:
    #         return
    # print("GPS OK")
    # after = datetime.now()
    # if (after - before).total_seconds() > 1.0:
    #     print("It took " + str((after - before).total_seconds())
    #           + " seconds to get GPS signal")
    # red_led.off()

    dt_before_meas = datetime.now()
    print("It took " + str((dt_before_meas - dt_start).total_seconds())
          + " seconds to initialize")
    log_memory_usage(log_file)

    return


def start():
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
        red_led.off()
        log_file.write("timestamp,memory_usage_mb\n")
        atcs = ATCommandSender(connection)

        init(atcs, log_file)
        if shutdown_requested:
            atcs.send_command("AT+CPOF")
            return
        if not measurements_started:
            return

        print("Starting measurements")
        green_led.on()
        with MeasurementsWriter(is_tmp=True, operator_info=atcs.get_operator()) as writer:
            writer.print_header()

            if shutdown_requested:
                atcs.send_command("AT+CPOF")
                return
            if not measurements_started:
                return

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
            gps_error = network_error = current_gps_error = current_network_error = False
            current_error_state = last_error_state = (current_gps_error, current_network_error)
            print("Measurements loop started")
            while measurements_started and not shutdown_requested:
                green_led.on()
                # Starting time is accurate to at least the second, I think.
                position_info = atcs.get_position(starting_time)
                serving_cell_list = atcs.get_serving_cell(starting_time)
                neighbour_cell_list = atcs.get_neighbour_cells(starting_time)

                dt_after_commands = datetime.now()

                for info in position_info:  # TODO: There really is no need for a loop here
                    if not info:  # If no position found
                        current_gps_error = True
                    else:
                        current_gps_error = False

                    writer.write_line(info.to_printable_string())

                # Not sure if in NSA 5G both should be written or only one.
                for cell in serving_cell_list:
                    if not cell:  # If no network found
                        current_network_error = True
                    else:
                        current_network_error = False

                    writer.write_line(cell.to_printable_string())

                for cell in neighbour_cell_list:
                    writer.write_line(cell.to_printable_string())

                # Check if error state has changed to prevent resetting error blink
                current_error_state = (current_gps_error, current_network_error)
                if current_error_state != last_error_state:
                    gps_error = current_gps_error
                    network_error = current_network_error
                    update_error_led()
                    last_error_state = current_error_state

                dt_after_writing = datetime.now()
                print("Measurement ", str(current_measurement),
                      " took ", (dt_after_commands - starting_time).microseconds / 1000, " milliseconds ",
                      "and ", (dt_after_writing - dt_after_commands).microseconds,
                      " microseconds to save to file")

                starting_time = datetime.now()
                starting_time = starting_time + timedelta(microseconds=(1000000 - starting_time.microsecond))
                # half_time = starting_time + timedelta(microseconds=(1000000 / 2 - starting_time.microsecond))
                # pause.until(half_time)
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
                        print("Measurements stopped by user command")

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
          Button("GPIO25", pull_up=True, bounce_time=0.1, hold_time=3) as start_button
          ):
        start_button.when_held = shutdown
        start_button.when_released = start_measurements

        # red led continuously
        red_led.on()
        # Check if the module is connected by checking the device file
        # Red will be lit on boot until the module is properly connected
        print("Waiting for module")
        while not os.path.exists(module_path):
            time.sleep(0.5)
        print("Module found")
        red_led.off()

        green_led.on()
        print("Press start button to start measurements")
        while not shutdown_requested:
            if measurements_started:
                start()
                if not shutdown_requested:
                    print("Press start button to start a new measurements")
                    green_led.on()
            time.sleep(0.5)

    # When shutdown is requested, wait the measurement session to end, reach end of context (close leds and buttons)
    # and shutdown
    print("Shutting down now")
    os.system("sudo shutdown -h now")
