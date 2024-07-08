from time import sleep

import serial


class SerialConnection:
    def __init__(
            self,
            port_path,
            baudrate=115200,  # 460800
            timeout=5,  # Doesn't seem to be used in readline function
            encoding="ISO-8859-1"
            # encoding='utf-8',
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
        """
        self.port: str = port_path
        self.baudrate: int = baudrate
        self.timeout: float = timeout
        self.encoding: str = encoding
        self.module: serial.Serial | None = None

    def __enter__(self):
        """
        Open a serial connection. Will loop until a connection can be established.
        Sometimes it can take a dozen seconds on start up of the module, while the connection is still in the "busy"
        state. If the serial port is used by another process or wasn't closed properly, will loop until it's closed.
        """
        while True:
            try:  # Try to open a connection, if exception is raised because connection is not possible, retry.
                self.module = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
                if self.module.is_open:
                    print("Serial connection opened.")
                    print("-------------------------------")
                    return self
                else:
                    raise ConnectionError("Couldn't open a connection to " + self.port)
            except serial.SerialException as e:
                print(f"Failed to open connection: {e}. Retrying in 3 seconds...")
                sleep(3)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close the serial connection when the "with" block is exited, normally or because of an exception

        When exiting because of an exception, this will power down the module through AT+CPOF command.
        """
        if exc_tb:
            print("Serial Connection closed because of an error")
            # This must only be in the automatic mode when the RPI is powered down as well
            # print("Powering down the module")
            # self.send_command("AT+CPOF")

        # Close the serial connection
        if self.module:
            self.module.close()

    def send_command(self, cmd: str):
        """
        Send a text (for example an AT command) through the serial port.
        :param cmd: the command (text) to send
        """
        if self.module:
            self.module.write((cmd.strip() + "\r\n").encode(self.encoding))

    def read_response(self) -> list[str]:
        """
        Read a response of an AT command from the module until "OK" or "ERROR" is found.
        :return: List of lines read
        """
        result = list()

        line: str = ""
        while not (line.endswith("OK") or line.endswith("ERROR")):
            line = self.module.readline().decode(self.encoding).strip()
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
            line = self.module.readline().decode(self.encoding).strip()
            if line not in ['\n', '\r\n', '']:
                result.append(line + "\n")
        return result
