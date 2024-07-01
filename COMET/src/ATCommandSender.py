import time
from datetime import datetime

from ATResponses import QENGServing, QENGNeighbour, CGPSINFO, COPS
from SerialConnection import SerialConnection


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
        Provides methods for sending specific AT commands and receiving responses in specialized format.\n
        NOTE: send_command() method works for any module but other methods are made specifically for SIM8262E 5 module

        :param SerialConnection connection: The serial connection to the module. Most likely uses ttyUSB2 as port path.
        """
        self.module = connection
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
        self.module.send_command(cmd)
        result = ""
        lines = self.module.read_response()
        for line in lines:
            result += line
        return result

    def get_gps_info(self) -> str:
        """
        Sends AT+CGPSINFO command to query module position. Result is "+CGPSINFO: ,,,,,,,," if no position found.
        :returns: string corresponding to the position line, the entire response if wrong format
        """
        self.module.send_command("AT+CGPSINFO")
        result = ""
        lines = self.module.read_response()
        for line in lines:
            if "+CGPSINFO" in line:
                result = line.strip()
                break
            else:
                result += line
        return result

    def enter_pin(self, pin: str) -> str:
        if not pin.isnumeric():
            print(pin + " isn't a PIN code (must be numbers)")
            return ""
        if not len(pin.strip()) == 4:
            print("A PIN code must be 4 numbers long (got" + str(len(pin.strip())) + ")")
            return ""

        self.module.send_command("AT+CPIN=" + pin.strip())
        print("Sent: AT+CPIN=" + pin.strip())
        result = ""
        lines = self.module.read_pin_response()
        for line in lines:
            result += line
            if line.endswith("ERROR"):
                return ""
        return result

    def restart_gps(self):
        self.module.send_command("AT+CGPS?")
        lines = self.module.read_response()
        current_gps = ""
        for line in lines:
            current_gps += line
        if "+CGPS: 1,1" in current_gps.strip():
            print("GPS already ON in standalone mode")
        else:
            print("Restarting GPS")
            self.module.send_command("AT+CGPS=0")
            self.module.read_response()
            print("GPS OFF")
            self.module.send_command("AT+CGPS=1,1")
            lines = self.module.read_response()
            for line in lines:
                print(line)
            print("GPS ON in standalone mode")

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
                # handle_response(response)
                if response.splitlines()[0].strip() != "+CGPSINFO: ,,,,,,,,":
                    print("Signal acquired, got: ")
                    print(response)
                    signal_acquired = True
                    break
                print("No GPS signal, waiting...")
                time.sleep(10)
            minutes_elapsed += 1
        return signal_acquired

    def get_operator(self) -> COPS:
        """

        :return:
        """
        lines = self.send_command('AT+COPS?').splitlines()
        for line in lines:
            if line.startswith("+COPS:"):
                return COPS.from_string(line)
