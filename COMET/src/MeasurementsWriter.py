import os
from datetime import datetime
from io import TextIOWrapper

from ATResponses import COPS, CGPSINFO, QENGServing, QENGNeighbour


class MeasurementsWriter:
    def __init__(self, dir_path: str = "./measurements/", filename: str = "measurement.csv", is_tmp: bool = False,
                 operator_info: COPS = None):
        """

        NOTE: Must be instantiated using a with statement as it doesn't provide a dedicated close() method
        :param dir_path:
        :param filename:
        :param is_tmp:
        :param operator_info:
        """
        now = datetime.now()
        date_dir = now.strftime("%d-%m-%Y")
        file_prefix = now.strftime("%H-%M_")

        self.operator_info: COPS = operator_info

        self.dir_path: str = os.path.abspath(dir_path + date_dir + "/") + "/"
        self.filename: str = file_prefix + filename
        self.is_tmp: bool = is_tmp

        self.file_content: str = ""  # TODO: Remove this! It's memory AND processor intensive on long measurements
        # Can even potentially break the program when concatenating the string will take more than 1 second

        self.file: TextIOWrapper | None = None

    def __enter__(self):
        """
        Creates a file in the specified directory (which is created if doesn't exist) on "with" statement
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        """
        Closes the file when the "with" statement is exited (normally or because of an exception)
        :param exc_type:
        :param exc_val:
        :param traceback:
        """
        if self.file:
            self.file.close()

    def open(self):
        if not os.path.isdir(self.dir_path):
            os.makedirs(self.dir_path)

        if self.is_tmp:
            self.file = open(self.dir_path + "tmp_" + self.filename, "w")
        else:
            self.file = open(self.dir_path + self.filename, "w")

    def close(self):
        """
        Close the file and erase saved file content from memory
        """
        if self.file:
            self.file.close()
        self.file_content = ""

    def write(self, text: str = ""):
        self.file.write(text)
        # self.file_content += text

    def write_line(self, line: str = ""):
        self.file.write(line + "\n")
        # self.file_content += (line + "\n")

    def get_file_path(self) -> str:
        if self.is_tmp:
            return self.dir_path + "tmp_" + self.filename
        else:
            return self.dir_path + self.filename

    def print_header(self):
        # self.write_line("TECHNO|" + self.operator_info.act.name)
        operator_name = "Unknown"
        if self.operator_info is not None:
            operator_name = self.operator_info.operator_name
        header = ("HEADER\n"
                  "VERSION|1.0\n"
                  f"DATE|{datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
                  f"OPERATOR|{operator_name}\n"
                  "GPS_LOST|\n"
                  "GPS|TIMESTAMP|LATITUDE|LONGITUDE|ALTITUDE\n"
                  "MEASURE_SERVING|TIMESTAMP|NETWORK_TYPE|TAC|CELLID|MCC|MNC|PCID|EARFCN|RSRQ|RSRP|RSSI|SINR|IS_EN_DC\n"
                  "MEASURE_NEIGHBOUR_INTRA|TIMESTAMP|NETWORK_TYPE|PCID|EARFCN|RSRQ|RSRP|RSSI\n"
                  "MEASURE_NEIGHBOUR_INTER|TIMESTAMP|NETWORK_TYPE|PCID|EARFCN|RSRQ|RSRP|RSSI\n"
                  "\n"
                  "MEASUREMENTS\n")
        self.write(header)

    def print_gps_measurement(self, info: CGPSINFO):
        self.write_line(info.to_printable_string())

    def print_serving_cell_measurement(self, info: QENGServing):
        self.write_line(info.to_printable_string())

    def print_neighbour_cell_measurement(self, info: QENGNeighbour):
        self.write_line(info.to_printable_string())

    @staticmethod
    def add_gps_lost_header(file_path: str, gps_lost: bool):
        """
        Add information about whether the GPS signal was lost during measurements or not to the measurement file header.

        This will rewrite the file at `file_path` with lines of text given by `file_content`,
        while adding YES or NO to the GPS_LOST entry in the header depending on `gps_lost` parameter

        This function rewrites the entire file and can take fairly long time to write on big files.
        For example on a file with 1 hour of measurements it could take around 100ms or more.

        :param file_path: absolute or relative path to the measurement file to modify
        :param gps_lost: if True then write GPS_LOST|YES to header, if False write GPS_LOST|NO
        """
        with open(file_path, "r") as file:
            lines = file.readlines()

        if len(lines) < 10:
            print(f"ERROR: Tried adding GPS lost entry to an empty or non-measurement file: {file_path}")
            print(f"Measurements file will not be modified")
            return

        with open(file_path, "w") as file:
            if gps_lost:
                lines[4] = "GPS_LOST|YES\n"
            else:
                lines[4] = "GPS_LOST|NO\n"

            file.writelines(lines)


if __name__ == '__main__':
    pass
