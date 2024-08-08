import logging
import os
from datetime import datetime
from time import sleep

import serial

from shared.utils import print_to_logger_or_stdout


def setup_raw_at_logger():
    """
    Set up a logger to log all lines of AT command responses to the `raw_AT.log` file.

    :return: Logger for the raw AT output
    """
    log_dir_path = os.path.abspath(f'./logs/{datetime.now().strftime("%Y-%m-%d")}')
    if not os.path.isdir(log_dir_path):
        os.makedirs(log_dir_path)

    res = logging.getLogger("AT")

    formatter = logging.Formatter(fmt='[%(asctime)s]: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
    handler = logging.FileHandler(f'{log_dir_path}/raw_AT.log')
    handler.setFormatter(formatter)

    res.setLevel(logging.DEBUG)
    res.addHandler(handler)

    return res


class SerialConnection:
    def __init__(
            self,
            port_path: str,
            baudrate: int = 115200,
            timeout: float = 5,  # Doesn't seem to be used in readline function
            encoding: str = "ISO-8859-1",
            error_logger: logging.Logger = None,
            setup_raw_logger: bool = False,
    ):
        """
        Opens a serial connection to a device and provides methods to send AT commands to it and receive responses
        :param port_path: Path to the serial port on computer (ex: /dev/ttyUSB2)
        :param baudrate: Amount of bits/s going through the serial port. Depending on the baud rate, responses from the
            module can arrive deformed, 115200 seems to be working well. Possible values are: 300, 600, 1200, 2400,
            4800, 9600, 19200, 23400, 38400, 57600, 115200, 460800, 912600
        :param timeout: Affects reading responses from module. Setting it too low or too high
            might block the connection, especially when the module was just powered up.
        :param encoding: How the text going through the serial port is encoded and decoded,
            for example utf-8 or ISO-8859-1
        :param error_logger: If given, will log errors (on enter and exit). If not, will print them to console
        :param setup_raw_logger: If True, will set up a logger to log all AT command responses to a file
        """
        self.port = port_path
        self.baudrate = baudrate
        self.timeout = timeout
        self.encoding = encoding
        self.module: serial.Serial | None = None

        self.error_logger: logging.Logger | None = error_logger
        self.raw_logger: logging.Logger | None = None
        if setup_raw_logger:
            self.raw_logger = setup_raw_at_logger()
            self.raw_logger.info("\n\n\n")  # A few empty lines for separation

    def __enter__(self):
        """
        Open a serial connection. Will loop until a connection can be established.
        Sometimes it can take a dozen seconds on start up of the module, while the connection is still in the "busy"
        state. If the serial port is used by another process or wasn't closed properly, will loop until it's open.
        """
        while True:
            try:  # Try to open a connection, if exception is raised because connection is not possible, retry.
                self.module = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
                if self.module.is_open:
                    print_to_logger_or_stdout("Serial connection opened.", logger=self.raw_logger)
                    print_to_logger_or_stdout("-------------------------------", logger=self.raw_logger)
                    return self
                else:
                    raise ConnectionError("Couldn't open a connection to " + self.port)
            except serial.SerialException as e:
                print_to_logger_or_stdout(f"Failed to open connection: {e}. Retrying in 3 seconds...",
                                          logger=self.error_logger)
                sleep(3)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close the serial connection when the "with" block is exited, normally or because of an exception

        When exiting because of an exception, this will power down the module through AT+CPOF command.
        """
        if exc_tb:
            print_to_logger_or_stdout("Serial connection closed because of an error",
                                      logger=self.error_logger, severity_level=logging.CRITICAL)
            # This must only be in the automatic mode when the RPI is powered down as well
            print_to_logger_or_stdout("Powering down the module", logger=self.error_logger)
            self.send_command("AT+CPOF")

        # Close the serial connection
        if self.module:
            self.module.close()

    def readline(self) -> str:
        """
        Read a line in binary from the module and return the decoded string corresponding to that line.

        If instance has a raw logger, the line will also be logged to it.

        :return: String corresponding to the line read, decoded with SerialConnection.encoding
        """
        line = self.module.readline().decode(self.encoding, errors='ignore')
        if self.raw_logger is not None:
            self.raw_logger.debug(line)
        return line

    def send_command(self, cmd: str):
        """
        Send a text (for example an AT command) through the serial port. Logs the command sent if raw logger is given.
        :param cmd: the command (text) to send
        """
        if self.module:
            self.module.write((cmd.strip() + "\r\n").encode(self.encoding))
            if self.raw_logger is not None:
                self.raw_logger.info(f"Sent: {cmd}")

    def read_response(self) -> list[str]:
        """
        Read a response of an AT command from the module until "OK" or "ERROR" is found.
        :return: List of lines read
        """
        result = list()

        line: str = ""
        while not (line.endswith("OK") or line.endswith("ERROR") or "CME ERROR" in line):
            line = self.readline().strip()
            if line not in ['\n', '\r\n', '']:
                result.append(line + "\n")

        return result

    def read_pin_response(self) -> list[str]:
        """
        Read the response of the AT+CPIN=XXXX command. When sending AT+CPIN=XXXX command, this method must be used
        as the response continues after the OK line, unlike most other commands.

        In this method the response is read until either "PB DONE" or "ERROR" but as the exact format of the response
        is not documented, it's not sure to always work correctly.

        :return: List of lines read
        """
        result = list()
        line: str = ""
        # AT+CPIN will send SMS DONE and PB DONE after the initial OK
        while not ("PB DONE" in line or "ERROR" in line):
            line = self.readline().strip()
            if line not in ['\n', '\r\n', '']:
                result.append(line + "\n")
        return result
