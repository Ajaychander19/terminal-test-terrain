#!/usr/bin/python

"""
This script allows for manual sending of AT commands when executed
"""

from datetime import datetime
from datetime import timedelta

import pause

from ATCommandSender import ATCommandSender
from SerialConnection import SerialConnection
from MeasurementsWriter import MeasurementsWriter

import time


def check_for_network(atcs: ATCommandSender):
    """
    Checks for network signal, looping until it is found.

    In most cases it is instant, but sometimes it can last for 3-10 seconds on start up. Will loop infinitely if no
    network can be found for example when the SIM card is not activated or the module is forced in a network mode
    not available locally (for example when forced to 5G when no 5G cells are present)

    :param atcs: An instance of an initialized ATCommandSender
    """
    network_ok = "NO SERVICE" not in atcs.send_command('AT+CPSI?')
    if not network_ok:
        print("No service, waiting...")
    while not network_ok:
        time.sleep(1)  # CPSI is easy enough to do every second
        network_ok = "NO SERVICE" not in atcs.send_command('AT+CPSI?')

    print("Service OK")


def check_for_gps(atcs: ATCommandSender):
    """
    Checks for GPS in a loop until a position is found.

    This function can take anywhere from nearly instant (if a GPS fix is already acquired) to 3-4 minutes on average
    on start up of the module or even 10-15 minutes in the worst case (when the module has never got a GPS fix before)

    :param atcs: An instance of an initialized ATCommandSender
    """
    signal_acquired = False
    while not signal_acquired:
        print("Trying to acquire GPS signal...")
        signal_acquired = (atcs.get_gps_info() != "+CGPSINFO: ,,,,,,,,")
        time.sleep(10)
    print("GPS OK")


def unlock_sim():
    """
    Checks if the SIM card is unlocked, if not ask user for PIN code and try to unlock it.

    Alerts if the PIN was wrong and shows how many attempts are left.

    With given pin code, tries to unlock the SIM card every 10 seconds and checks for its readiness every second because
    it cas take some time before the SIM card is activated after the PIN code has been sent. If the PIN code was wrong,
    shows the attempts left and asks again.

    On average, this function takes 3 seconds to finish on start up and is nearly instant if the SIM card has
    already been activated
    """
    sim_ready = "READY" in ATCS.send_command("AT+CPIN?")
    while not sim_ready:
        nb_left = ATCS.get_pin_times()
        pin_code = input(f"Enter the PIN code (you have {nb_left} attempts left): \n").strip()
        if len(pin_code) != 4 or not pin_code.isnumeric():  # Retry if incorrect format
            print("Incorrect PIN code format! Must be 4 numeric characters long, for example 0000)")
            continue

        cpt = 10  # Try to unlock sim every 10 seconds. Not sure if it's necessary.
        while not sim_ready:
            if cpt == 10:
                cpt = 0
                print("Trying to unlock...")
                pin_accepted = ATCS.enter_pin(pin_code)
                # If nb attempts decreased, pin was wrong, re-ask pin
                if not pin_accepted:
                    print("Wrong PIN code!")
                    break

            time.sleep(1)
            cpt += 1
            sim_state = ATCS.send_command("AT+CPIN?")
            sim_ready = "READY" in sim_state


if __name__ == '__main__':
    dt = datetime.now()
    print("Starting date and time is: ", dt)

    with SerialConnection('/dev/ttyUSB2') as connection:
        ATCS = ATCommandSender(connection)

        print("Waiting 30 seconds to let module finish initializations...")
        for i in range(30):
            time.sleep(1)

        first_time = input("Do you want to setup the module? (yes/no)\n").strip()
        if first_time.lower() == "yes" or first_time.lower() == "y":
            unlock_sim()
            print("SIM card ready")

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

            check_for_network(atcs=ATCS)

            setup_gps = input("Do you want to setup the GPS and wait for a fix? (yes/no)\n").strip()
            if setup_gps.lower() == "yes" or setup_gps.lower() == "y":
                ATCS.setup_gps()
                check_for_gps(atcs=ATCS)

            print("Setup complete")

        while True:
            command = input("type the command to send "
                            "(\n"
                            "* 'stop' to end the program execution\n"
                            "* 'powerdown' to end the program execution and power down the module\n"
                            "* 'measurements n' to start measurements for n second. "
                            "If no GPS signal, will wait for it\n"
                            "* 'gps' to wait until a GPS signal is found\n"
                            "* any AT command to get a response\n"
                            "): \n").strip()
            if command == "powerdown":
                powerdown = True
                break
            if command == "stop":
                break
            if "measurement" in command:
                # TODO: add proper logging
                arguments = command.split()
                if len(arguments) != 2:
                    print("Incorrect measurement command (must have one and only numeric argument): " + command)
                    break

                check_for_gps(atcs=ATCS)

                print("Starting measurements")
                with MeasurementsWriter(operator_info=ATCS.get_operator()) as writer:
                    writer.print_header()

                    timeout = int(arguments[1])  # in seconds
                    measurements_duration_elapsed = 0

                    # Wait until the start of the second to get a nice round number
                    starting_time = datetime.now()
                    starting_time = starting_time + timedelta(microseconds=(1000000 - starting_time.microsecond))
                    pause.until(starting_time)

                    while measurements_duration_elapsed < timeout:
                        dt_after_commands = datetime.now()

                        # Print GPS
                        writer.print_gps_measurement(ATCS.get_position(starting_time))

                        # Print serving cell (two of them if in EN-DC mode)
                        for cell in ATCS.get_serving_cell(starting_time):
                            writer.print_serving_cell_measurement(cell)

                        # Print neighbouring cells
                        for cell in ATCS.get_neighbour_cells(starting_time):
                            writer.print_neighbour_cell_measurement(cell)

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
                if len(arguments) != 1:
                    print("gps command doesn't require arguments, got: " + command + " instead")
                    break
                check_for_gps(atcs=ATCS)
                continue

            dt_before = datetime.now()
            print("The response is:")
            print("-------------------------------")
            print(ATCS.send_command(command))
            print("-------------------------------")
            print()

            dt_after = datetime.now()
            print(command + " done at: ", dt_after)
            print("It took ", (dt_after - dt_before).microseconds, " microseconds\n")

        if powerdown:
            ATCS.send_command("AT+CPOF")
