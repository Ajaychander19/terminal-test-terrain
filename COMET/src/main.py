import sys
from datetime import datetime
from datetime import timedelta

import pause

from ATCommandSender import ATCommandSender, handle_response
from SerialConnection import SerialConnection
from FileWriters import MeasurementsWriter

import time

if __name__ == '__main__':
    dt = datetime.now()
    print("Starting date and time is:", dt)

    with SerialConnection('/dev/ttyUSB2') as connection:
        ATCS = ATCommandSender(connection)
        dt = datetime.now()
        print("Connection opened at :", dt)

        # Apparently before sending any commands I must check if "RDY" is received? Not sure if it's really necessary
        # but documentation says so...

        timeout = 0
        first_time = input("Is this script being executed for the first time since powering up the module? (yes/no)\n")
        if first_time.lower() == "yes" or first_time.lower() == "y":
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

            timeout = 0
            while "READY" not in ATCS.send_command("AT+CPIN?"):
                print("SIM not ready, retrying...")
                time.sleep(10)
                if "READY" not in ATCS.send_command("AT+CPIN?"):
                    ATCS.enter_pin("0000")
                timeout += 10
                if timeout >= 60:
                    sys.exit("Couldn't connect to the SIM, aborting (waited for 60 seconds)")

            mode = input("type the network mode to use "
                         "(\n"
                         "* 'LTE' for LTE only\n"
                         "* 'NR5G' for NR5G only\n"
                         "* 'BOTH' for LTE+NR5G only\n"
                         "* Automatic by default\n"
                         "): \n").strip().upper()
            if 'LTE' in mode:
                print("Setting LTE only mode")
                ATCS.send_command('AT+CNMP=38')
            elif 'NR5G' in mode:
                print("Setting NR5G only mode")
                ATCS.send_command('AT+CNMP=71')
            elif 'BOTH' in mode:
                print("Setting LTE+NR5G only mode")
                ATCS.send_command('AT+CNMP=109')
            else:
                print("Defaulting to automatic mode")
                ATCS.send_command('AT+CNMP=2')

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
        print("GPS OK")

        while True:
            command = input("type the command to send "
                            "(\n"
                            "* 'stop' to end the program execution\n"
                            "* 'measurements n' to start measurements for n seconds (will try to get GPS signal for "
                            "10 minutes if no signal)\n"
                            "* 'gps n' to start acquiring gps signal for n minutes\n"
                            "* any AT command to get a response\n"
                            "): \n").strip()
            if command == "stop":
                break
            if "measurement" in command:
                arguments = command.split()
                if len(arguments) != 2:
                    print("Incorrect measurement command (must have one and only numeric argument): " + command)
                    break

                if not gps_signal_acquired:
                    print("Trying to acquire GPS signal...")
                    gps_signal_acquired = ATCS.get_gps_signal(10)
                    if not gps_signal_acquired:
                        print("Couldn't acquire GPS signal, aborting measurements")
                print("Starting measurements")
                with MeasurementsWriter(is_tmp=True, operator_info=ATCS.get_operator()) as writer:
                    writer.print_header()

                    timeout = int(arguments[1])  # in seconds
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

                        # FIXME: this should logically be a method of writer class
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
                    continue

            if "gps" in command:
                arguments = command.split()
                if len(arguments) != 2:
                    print("gps command must have one and only numeric argument got: " + command + " instead")
                    break
                print("Attempting to acquire a GPS signal")
                gps_signal_acquired = ATCS.get_gps_signal(int(arguments[1]))
                if gps_signal_acquired:
                    print("GPS Signal acquired")
                else:
                    print("Couldn't get a GPS satellite fix")
                continue

            dt_before = datetime.now()
            handle_response(ATCS.send_command(command))

            dt_after = datetime.now()
            print(command + " done at: ", dt_after)
            print("It took ", (dt_after - dt_before).microseconds, " microseconds\n")

        # Power down the module
        ATCS.send_command("AT+CPOF")
