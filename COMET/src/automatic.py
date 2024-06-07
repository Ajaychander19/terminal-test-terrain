import os
import sys
import time
from datetime import datetime, timedelta

import pause

from FileWriters import MeasurementsWriter
from SerialConnection import SerialConnection
from ATCommandSender import ATCommandSender

if __name__ == '__main__':
    print("Waiting 10 seconds on start-up just in case")
    time.sleep(10)

    with SerialConnection('/dev/ttyUSB2') as connection:
        ATCS = ATCommandSender(connection)

        timeout = 0
        sim_ready = "READY" in ATCS.send_command("AT+CPIN?")
        while not sim_ready:
            print("SIM not ready, trying to activate...")
            ATCS.enter_pin("0000")
            time.sleep(10)
            sim_ready = "READY" in ATCS.send_command("AT+CPIN?")

            timeout += 10
            if timeout >= 180:
                sys.exit("Couldn't activate the SIM, aborting (waited for 180 seconds)")
        print("SIM card ready")

        print("Defaulting to LTE only mode")
        ATCS.send_command('AT+CNMP=38')

        timeout = 0
        while "NO SERVICE" in ATCS.send_command('AT+CPSI?'):  # CPSI car plus léger
            print("No service, waiting...")
            time.sleep(10)
            timeout += 10
            if timeout >= 600:
                sys.exit("Couldn't connect to mobile network, aborting (waited for 600 seconds)")
        print("Service OK")

        ATCS.restart_gps()

        gps_signal_acquired = False
        if not gps_signal_acquired:
            print("Trying to acquire GPS signal...")
            gps_signal_acquired = ATCS.get_gps_signal(30)  # Try to get a signal for 30 minutes
            if not gps_signal_acquired:
                sys.exit("Couldn't acquire GPS signal, aborting measurements (waited for 30 minutes)")
        print("GPS OK")

        print("Starting measurements")
        with MeasurementsWriter(is_tmp=True, operator_info=ATCS.get_operator()) as writer:
            writer.print_header()

            timeout = 3600  # 60 minutes
            measurements_duration_elapsed = 0

            # Wait until the start of the second to get a nice round number
            starting_time = datetime.now()
            starting_time = starting_time + timedelta(microseconds=(1000000 - starting_time.microsecond))
            pause.until(starting_time)

            file_time = None
            try:
                file_time = os.stat("./stop").st_ctime
            except OSError:
                pass

            end_loop = False
            while measurements_duration_elapsed < timeout and not end_loop:
                # Starting time is accurate to at least the second, I think.
                position_info = ATCS.get_position(starting_time)
                serving_cell_list = ATCS.get_serving_cell(starting_time)
                neighbour_cell_list = ATCS.get_neighbour_cells(starting_time)

                dt_after_commands = datetime.now()

                for info in position_info:
                    writer.write_line(info.to_printable_string())

                # Not sure if in NSA 5G both should be written or only one.
                for cell in serving_cell_list:
                    writer.write_line(cell.to_printable_string())

                for cell in neighbour_cell_list:
                    writer.write_line(cell.to_printable_string())

                dt_after_writing = datetime.now()
                print("Measurement ", str(measurements_duration_elapsed),
                      " took ", (dt_after_commands - starting_time).microseconds / 1000, " milliseconds ",
                      "and ", (dt_after_writing - dt_after_commands).microseconds,
                      " microseconds to save to file")

                measurements_duration_elapsed += 1
                if file_time is not None:
                    # If the stop file was modified (by touch or else), stop the execution
                    if os.stat("./stop").st_ctime != file_time:
                        end_loop = True
                        print("Measurements stopped by user command")

                starting_time = datetime.now()
                starting_time = starting_time + timedelta(microseconds=(1000000 - starting_time.microsecond))
                pause.until(starting_time)

        # Power down the module
        ATCS.send_command("AT+CPOF")
