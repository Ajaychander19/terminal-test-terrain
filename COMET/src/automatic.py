import sys
import time
from datetime import datetime, timedelta

import pause

from FileWriters import MeasurementsWriter
from SerialConnection import SerialConnection
from ATCommandSender import ATCommandSender

if __name__ == '__main__':
    with SerialConnection('/dev/ttyUSB2') as connection:
        timeout = 0
        ATCS = ATCommandSender(connection)

        pin_ok = False
        print("Waiting 15 seconds on start-up just in case")
        while not pin_ok:
            time.sleep(15)
            response = ATCS.enter_pin("0000")  # response is empty if got an error
            pin_ok = (response != "")
            if not pin_ok:
                print("Couldn't connect to the SIM, retrying...")
            timeout += 15
            if timeout >= 60:
                sys.exit("Couldn't connect to the SIM, aborting (waited for 60 seconds)")
        time.sleep(5)

        timeout = 0
        while "READY" not in ATCS.send_command("AT+CPIN?"):
            print("SIM not ready, retrying...")
            time.sleep(10)
            if "READY" not in ATCS.send_command("AT+CPIN?"):
                ATCS.enter_pin("0000")
            timeout += 10
            if timeout >= 60:
                sys.exit("Couldn't connect to the SIM, aborting (waited for 60 seconds)")

        print("Defaulting to LTE only mode")
        ATCS.send_command('AT+CNMP=38')

        timeout = 0
        while "NO SERVICE" in ATCS.send_command('AT+CPSI?'):
            print("No service, waiting...")
            time.sleep(10)
            timeout += 10
            if timeout >= 120:
                sys.exit("Couldn't get a signal, aborting (waited for 120 seconds)")
        print("Service OK")

        ATCS.restart_gps()

        gps_signal_acquired = False
        if not gps_signal_acquired:
            print("Trying to acquire GPS signal...")
            gps_signal_acquired = ATCS.get_gps_signal(10)
            if not gps_signal_acquired:
                print("Couldn't acquire GPS signal, aborting measurements")

        print("Starting measurements")
        with MeasurementsWriter(is_tmp=True, operator_info=ATCS.get_operator()) as writer:
            writer.print_header()

            timeout = 30
            measurements_duration_elapsed = 0

            # Wait until the start of the second to get a nice round number
            starting_time = datetime.now()
            starting_time = starting_time + timedelta(microseconds=(1000000 - starting_time.microsecond))
            pause.until(starting_time)

            while measurements_duration_elapsed < timeout:
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

                measurements_duration_elapsed += 1

                dt_after_writing = datetime.now()
                print("Measurement ", str(measurements_duration_elapsed),
                      " took ", (dt_after_commands - starting_time).microseconds / 1000, " milliseconds ",
                      "and ", (dt_after_writing - dt_after_commands).microseconds,
                      " microseconds to save to file")

                starting_time = datetime.now()
                starting_time = starting_time + timedelta(microseconds=(1000000 - starting_time.microsecond))
                pause.until(starting_time)

        # Power down the module
        ATCS.send_command("AT+CPOF")
