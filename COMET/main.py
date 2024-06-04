from datetime import datetime
from datetime import timedelta

import pause

from SerialConnection import SerialConnection
from FileWriters import MeasurementsWriter

from ATResponses import QENGServing
from ATResponses import QENGNeighbour
from ATResponses import CGPSINFO
from ATResponses import COPS

import time


def handle_response(response: str) -> None:
    print("The response is:")
    print("-------------------------------")
    print(response)
    print("-------------------------------\n")


class ATCommandSender:
    """
    Class for sending AT commands to a device and receiving responses
    """

    def __init__(self, connection: SerialConnection):
        """
        Initialize and open the serial connection.

        :param SerialConnection connection: The serial connection to the modem. Most likely uses ttyUSB2 as port path.
        """
        self.modem = connection
        ""

    def send_command(self, cmd: str) -> str:
        """
        Sends cmd
        :param str cmd: the AT command to send, for example cmd="AT+CSQ"
        :returns: string corresponding to the lines of the response
        """
        if not cmd.lower().startswith("at"):
            print(cmd + " isn't an AT command")
            return ""
        self.modem.send_command(cmd)
        # print("Sent: " + cmd)
        result = ""
        lines = self.modem.read_response()
        for line in lines:
            result += line
        return result

    def enter_pin(self, pin: str) -> str:
        if not pin.isnumeric():
            print(pin + " isn't a PIN code (must be numbers)")
            return ""
        if not len(pin.strip()) == 4:
            print("A PIN code must be 4 numbers long (got" + str(len(pin.strip())) + ")")
            return ""

        self.modem.send_command("AT+CPIN=" + pin.strip())
        print("Sent: AT+CPIN=" + pin.strip())
        result = ""
        lines = self.modem.read_pin_response()
        for line in lines:
            result += line
            if line.endswith("ERROR"):
                return ""
        return result

    def restart_gps(self):
        self.modem.send_command("AT+CGPS=0")
        self.modem.read_response()
        print("GPS OFF")
        self.modem.send_command("AT+CGPS=1,1")
        lines = self.modem.read_response()
        for line in lines:
            print(line)
        print("GPS ON in UE-assisted mode")

    def get_serving_cell(self, timestamp: datetime = None) -> list[QENGServing]:
        lines: list[str] = self.send_command('AT+QENG="servingcell"').splitlines()
        # Can hold 2 instances if in EN-DC mode
        list_serving: list[QENGServing] = list()
        for line in lines:
            if line.startswith("+QENG"):
                list_serving.append(QENGServing.from_string(line, timestamp))
        cleaned_list = [x for x in list_serving if x is not None]
        return cleaned_list

    def get_neighbour_cells(self, timestamp: datetime = None) -> list[QENGNeighbour]:
        lines: list[str] = self.send_command('AT+QENG="neighbourcell"').splitlines()
        list_neighbour: list[QENGNeighbour] = list()
        for line in lines:
            if line.startswith("+QENG"):
                list_neighbour.append(QENGNeighbour.from_string(line, timestamp))
        cleaned_list = [x for x in list_neighbour if x is not None]
        return cleaned_list

    def get_position(self, timestamp: datetime = None) -> list[CGPSINFO]:
        lines: list[str] = self.send_command('AT+CGPSINFO').splitlines()
        list_serving: list[CGPSINFO] = list()
        for line in lines:
            if line.startswith("+CGPSINFO:"):
                list_serving.append(CGPSINFO.from_string(line, timestamp))
        cleaned_list = [x for x in list_serving if x is not None]
        return cleaned_list

    def get_gps_signal(self, minutes: int) -> bool:
        signal_acquired = False
        minutes_elapsed = 0

        if int(minutes) == 0:
            response = self.send_command('AT+CGPSINFO')
            return response.splitlines()[0].strip() != "+CGPSINFO: ,,,,,,,,"

        while not signal_acquired and minutes_elapsed < minutes:
            for i in range(6):
                response = self.send_command('AT+CGPSINFO')
                handle_response(response)
                if response.splitlines()[0].strip() != "+CGPSINFO: ,,,,,,,,":
                    print("Signal acquired, got: ")
                    print(response)
                    signal_acquired = True
                    break
                time.sleep(10)
            minutes_elapsed += 1
        return signal_acquired

    def get_operator(self) -> COPS:
        lines: list[str] = self.send_command('AT+COPS?').splitlines()
        for line in lines:
            if line.startswith("+COPS:"):
                return COPS.from_string(line)


if __name__ == '__main__':
    dt = datetime.now()
    print("Starting date and time is:", dt)

    with SerialConnection('/dev/ttyUSB2') as connection:
        ATCS = ATCommandSender(connection)
        dt = datetime.now()
        print("Connection opened at :", dt)

        # Apparently before sending any commands I must check if "RDY" is received? Not sure if it's really necessary
        # but documentation says so...
        print("Testing if AT commands are working")
        handle_response(ATCS.send_command("AT+CSQ"))

        first_time = input("Is this script being executed for the first time since powering up the modem? (yes/no)\n")
        if first_time.lower() == "yes" or first_time.lower() == "y":
            pin_ok = False
            print("Waiting 10 seconds on start-up just in case")
            while not pin_ok:
                time.sleep(10)
                response = ATCS.enter_pin("0000")  # response is empty if got an error
                pin_ok = (response != "")
                if not pin_ok:
                    print("Couldn't connect to the SIM, retrying...")
            time.sleep(5)
        #     while "READY" not in ATCS.send_command("AT+CPIN?"):
        #         print("SIM not ready, retrying...")
        #         ATCS.enter_pin("0000")
        #         time.sleep(10)
        #
        # while "NO SERVICE" in ATCS.send_command('AT+CPSI?'):
        #     print("No service, waiting...")
        #     time.sleep(10)
        # print("Service OK")

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
            print("It took ", (dt_after - dt_before).microseconds, " microseconds")
