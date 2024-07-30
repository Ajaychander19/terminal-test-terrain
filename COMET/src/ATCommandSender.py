import logging
from datetime import datetime

from ATResponses import QENGServing, QENGNeighbour, CGPSINFO, COPS
from SerialConnection import SerialConnection
from Utils import print_to_logger_or_stdout


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
        ""

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

    def enter_pin(self, pin: str, logger: logging.Logger = None) -> str:
        """
        Send AT+CPIN=pin command. Will return the entire response on success and empty string on error.

        :param logger: If not None, will log errors and will raise an exception (to be used in automatic mode).
        :param pin: The pin code of the SIM card. Must be 4 characters long, with numeric characters only,
            for example "0000".
        :return: A multiline string containing the lines of the response.
        """
        if not pin.isnumeric():
            if logger is not None:
                logger.error(f"Incorrect pin ({pin.strip()}) was used, must be numeric")
                raise PinException
            else:
                print(f"{pin} isn't a PIN code (must be numbers)")
            return ""
        if not len(pin.strip()) == 4:
            if logger is not None:
                logger.error(f"Incorrect pin ({pin.strip()}) was used, must 4 characters long")
                raise PinException
            else:
                print(f"A PIN code must be 4 numbers long (got {str(len(pin.strip()))})")
            return ""

        self.module.send_command("AT+CPIN=" + pin.strip())
        print_to_logger_or_stdout(f"Sent: AT+CPIN={pin.strip()}", logger=logger)

        result = ""
        lines = self.module.read_pin_response()
        for line in lines:
            result += line
            if line.endswith("ERROR"):
                return ""
        return result

    def setup_gps(self, logger: logging.Logger = None):
        """
        Restart a GPS session in standalone mode.

        :param logger: If not None, will log GPS restarting.
        """
        if "+CGPS: 1,1" in self.send_command("AT+CGPS?").strip():
            print_to_logger_or_stdout("GPS already ON in standalone mode", logger=logger)
        else:
            print_to_logger_or_stdout("GPS session in wrong mode, restarting GPS", logger=logger)

            self.send_command("AT+CGPS=0")
            print_to_logger_or_stdout("GPS session OFF", logger, severity_level=logging.DEBUG)

            self.send_command("AT+CGPS=1,1")
            print_to_logger_or_stdout("GPS ON in standalone mode", logger=logger)

        if "+CGPSAUTO: 1" not in self.send_command("AT+CGPSAUTO?").strip():
            print_to_logger_or_stdout("Setting GPS to start automatically in standalone mode", logger=logger)
            self.send_command("AT+CGPSAUTO=1")

        if "31,1" not in self.send_command("AT+CGNSSMODE?").strip():
            if "+CGPS: 0" not in self.send_command("AT+CGPS?").strip():
                print_to_logger_or_stdout("Setting GNSS mode to all types and dpo (31,1)", logger=logger)
                self.send_command("AT+CGPS=0")
                self.send_command("AT+CGNSSMODE=31,1")
                self.send_command("AT+CGPS=1,1")
        print_to_logger_or_stdout("GPS set up", logger=logger)

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
