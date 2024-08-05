import logging
from datetime import datetime

from ATResponses import QENGServing, QENGNeighbour, CGPSINFO, COPS
from SerialConnection import SerialConnection
from shared.utils import print_to_logger_or_stdout


class PinException(Exception):
    pass


class ATCommandSender:
    """
    Class for sending AT commands to a device and receiving responses
    """

    def __init__(self, connection: SerialConnection):
        """
        Provides methods for sending specific AT commands and receiving responses in specialized format.\n
        NOTE: send_command() method works for any module but other methods are made specifically for SIM8262E 5 module

        :param SerialConnection connection: An open serial connection to the module.
        """
        self.module = connection

    def send_command(self, cmd: str, logger: logging.Logger = None) -> str:
        """
        Send an AT command to the module and read the response. If cmd is in wrong format (doesn't start with AT),
        return empty string. If the command is not recognized by the module,
        it will be interpreted and the module will respond with "ERROR".

        :param logger: If not None, will log an error on unrecognized command
        :param str cmd: the AT command to send, for example cmd="AT+CSQ"
        :returns: a multiline string with all lines of the response
        """
        if not cmd.strip().upper().startswith("AT"):
            print_to_logger_or_stdout(f"{cmd} was sent to the module, which is not an AT command",
                                      logger=logger, severity_level=logging.ERROR)
            return ""
        self.module.send_command(cmd)

        result = ""
        lines = self.module.read_response()
        for line in lines:
            result += line
        return result

    def setup_gps(self, logger: logging.Logger = None):
        """
        Set up various GNSS modes if needed (auto start at boot, GPS only, NMEA output sentence type and rate,
         standalone mode)

        :param logger: If given, will log messages.
        """
        # Setting up GPS session auto start at boot
        if "+CGPSAUTO: 1" not in self.send_command("AT+CGPSAUTO?"):
            print_to_logger_or_stdout("Setting GPS to start automatically in standalone mode", logger=logger)
            self.send_command("AT+CGPSAUTO=1")

        # Setting up satellite systems used (GPS only)
        if "8,1" not in self.send_command("AT+CGNSSMODE?"):
            if "+CGPS: 0" not in self.send_command("AT+CGPS?"):
                print_to_logger_or_stdout("Stopping GPS session for configuration", logger=logger)
                self.send_command("AT+CGPS=0")

            print_to_logger_or_stdout("Setting GNSS mode to GPS only with DPO (8,1)", logger=logger)
            self.send_command("AT+CGNSSMODE=8,1")

        # Setting up NMEA output sentences type
        if "134655" not in self.send_command("AT+CGPSNMEA?"):
            if "+CGPS: 0" not in self.send_command("AT+CGPS?"):
                print_to_logger_or_stdout("Stopping GPS session for configuration", logger=logger)
                self.send_command("AT+CGPS=0")

            self.send_command("AT+CGPSNMEA=134655")
            print_to_logger_or_stdout("Setting NMEA output sentences to 134655", logger=logger)

        # Setting up NMEA output rate
        if "0" not in self.send_command("AT+CGPSNMEARATE?"):
            # No need to stop session for the output rate
            self.send_command("AT+CGPSNMEARATE=0")
            print_to_logger_or_stdout("Setting NMEA output rate to 1Hz", logger=logger)

        # Starting GPS session in correct mode
        gps_session_state = self.send_command("AT+CGPS?")
        if "+CGPS: 0" in gps_session_state:  # Start GPS if it's off
            self.send_command("AT+CGPS=1,1")
            print_to_logger_or_stdout("Starting GPS session in standalone mode", logger=logger)
        elif "+CGPS: 1,1" not in gps_session_state:  # Restart GPS if it's in wrong mode
            print_to_logger_or_stdout("GPS session in wrong mode, restarting GPS", logger=logger)
            self.send_command("AT+CGPS=0")
            print_to_logger_or_stdout("GPS session OFF", logger, severity_level=logging.DEBUG)
            self.send_command("AT+CGPS=1,1")
            print_to_logger_or_stdout("GPS ON in standalone mode", logger=logger)

        print_to_logger_or_stdout("GPS set up", logger=logger)

    def get_gps_info(self) -> str:
        """
        Sends AT+CGPSINFO command to query module position. Result is "+CGPSINFO: ,,,,,,,," if no position found.

        Despite what the AT command manual says, the +CGPSINFO: line is given before the OK line, not after.

        :returns: a single line with the localisation information (+CGPSINFO line), the entire response if an error
        occurred.
        """
        self.module.send_command("AT+CGPSINFO")
        result = ""
        lines = self.module.read_response()
        for line in lines:
            if "+CGPSINFO" in line:
                return line.strip()
            else:
                result += line
        return result

    def enter_pin(self, pin: str, logger: logging.Logger = None) -> bool:
        """
        Send AT+CPIN=pin command. Will return the entire response on success and empty string on error.

        :param logger: Logs the command sent.
        :param pin: The pin code of the SIM card. Must be 4 characters long, with numeric characters only,
            for example "0000".
        :return: True if PIN code was accepted, False on error (for example wrong pin).
        """
        self.module.send_command("AT+CPIN=" + pin.strip())
        print_to_logger_or_stdout(f"Sent: AT+CPIN={pin.strip()}", logger=logger)

        result = ""
        lines = self.module.read_pin_response()
        for line in lines:
            result += line
            if "ERROR" in line:
                return False
        return True

    def get_pin_times(self) -> int | None:
        """
        Use the AT+SPIC to retrieve the number of times left to enter the PIN code

        :return: number of times left to enter the PIN code. None if in case of error.
        """
        self.module.send_command("AT+SPIC")
        lines = self.module.read_response()
        for line in lines:
            line = line.strip()
            if line.startswith("+SPIC"):
                values: list[str] = line.removeprefix('+SPIC:').split(',')
                values = [value.strip() for value in values]
                return int(values[0])
        return None

    def get_serving_cell(self, timestamp: datetime = None) -> list[QENGServing]:
        """
        Send the AT+QENG="servingcell" command and retrieves a list of QENGServing instances holding the serving
        cell data

        :param timestamp: Defines the timestamp of the measurement. If None, uses datetime.now() as timestamp.
        :return: List of QENGServing instances holding the serving cell data.
            Has 2 instances in EN-DC mode and a single one in other modes.
        """
        lines: list[str] = self.send_command('AT+QENG="servingcell"').splitlines()
        lines = [x for x in lines if x.strip()]  # Remove empty lines
        list_serving: list[QENGServing] = list()  # Can hold 2 instances if in EN-DC mode

        if len(lines) == 1:
            if "ERROR" in lines[0]:
                list_serving.append(QENGServing.from_string(lines[0], timestamp))

        elif len(lines) == 2:  # Second line is "OK"
            list_serving.append(QENGServing.from_string(lines[0], timestamp))

        elif len(lines) == 4:  # EN-DC mode, last line is "OK"
            ue_state = QENGServing.get_ue_state_from_response(lines[0])
            list_serving.append(QENGServing.from_string(lines[1], timestamp, ue_state))
            list_serving.append(QENGServing.from_string(lines[2], timestamp, ue_state))

        # Only save valid instances. We still want the instances with no connection
        cleaned_list = [x for x in list_serving if x is not None]
        return cleaned_list

    def get_neighbour_cells(self, timestamp: datetime = None) -> list[QENGNeighbour]:
        """
        Send the AT+QENG="neighbourcell" command and retrieves a list of QENGNeighbour instances holding the
        data from all received neighbouring cells in LTE mode

        :param timestamp: Defines the timestamp of the measurement. If None, uses datetime.now() as timestamp.
        :return: List of QENGNeighbour instances holding data from all neighbouring cells in LTE mode, discarding
            WCDMA cells
        """
        lines: list[str] = self.send_command('AT+QENG="neighbourcell"').splitlines()
        list_neighbour: list[QENGNeighbour] = list()
        for line in lines:
            if line.startswith("+QENG"):
                list_neighbour.append(QENGNeighbour.from_string(line, timestamp))

        # Only save valid instances that are not in WCDMA mode
        cleaned_list = [x for x in list_neighbour if x is not None and x]
        return cleaned_list

    def get_position(self, timestamp: datetime = None) -> CGPSINFO | None:
        """
        Send the AT+CGPSINFO command to query the module's localisation.

        :param timestamp: Defines the timestamp of the measurement. If None, uses datetime.now() as timestamp.
        :return: An instance of CGPSINFO class filled with localisation information
        (can be empty if no fix was acquired), or None if no CGPSINFO response was found.
        """
        lines: list[str] = self.send_command('AT+CGPSINFO').splitlines()
        for line in lines:
            if line.startswith("+CGPSINFO:"):
                return CGPSINFO.from_string(line, timestamp)
        return None

    def get_operator(self) -> COPS:
        """
        Send AT+COPS? command to query the mobile operator on which the module is currently registered.

        :return: An instance of COPS class with the operator name
        """
        lines = self.send_command('AT+COPS?').splitlines()
        for line in lines:
            if line.startswith("+COPS:"):
                return COPS.from_string(line)
