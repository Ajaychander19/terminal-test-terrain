import serial


class SerialConnection:
    def __init__(
            self,
            port_path,
            baudrate=115200,  #460800
            timeout=5,
            encoding="ISO-8859-1"
            # encoding='utf-8',
    ):
        self.port: str = port_path
        self.baudrate: int = baudrate
        """115200 Default buad rate
        300,600,1200,2400,4800,9600,19200,38400,57600,115200,
        23400,460800,912600 Low speed baud rate
        3000000 High speed baud rate"""
        self.timeout: int = timeout
        self.encoding: str = encoding
        self.modem: serial.Serial | None = None

    def __enter__(self):
        # Open the serial connection
        self.modem = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        if self.modem.is_open:
            print("Serial connection opened.")
            print("-------------------------------")
        else:
            raise ConnectionError("Couldn't open a connection to " + self.port)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Close the serial connection
        if self.modem:
            self.modem.close()

        if exc_tb:
            print("Serial Connection closed because of an error: ", exc_tb)

    def send_command(self, cmd: str) -> None:
        if self.modem:
            self.modem.write((cmd + "\r\n").encode('utf-8'))

    # TODO: add a try-except for timeout
    def read_response(self) -> list:
        result = list()
        if not self.modem:
            return result

        line: str = ""
        while not (line.endswith("OK") or line.endswith("ERROR")):
            line = self.modem.readline().decode('utf-8').strip()
            if line not in ['\n', '\r\n', '']:
                result.append(line + "\n")
        return result

    def read_pin_response(self) -> list:
        result = list()
        line: str = ""
        # I'm not sure what are the rules for ending this. What I usually get is
        # OK +CPIN: READY SMS DONE PB DONE
        # But I'm not sure if it's reliable.
        while not ("PB DONE" in line or line.endswith("ERROR")):
            line = self.modem.readline().decode('utf-8').strip()
            if line not in ['\n', '\r\n', '']:
                result.append(line + "\n")
        return result
