import logging
import os
from datetime import datetime
from io import TextIOWrapper

from ATResponses import COPS, CGPSINFO, QENGServing, QENGNeighbour


class MeasurementsWriter:
    def __init__(self, dir_path: str = "./measurements/", filename_suffix: str = "measurement", is_tmp: bool = False,
                 operator_info: COPS = None):
        """
        Class for writing measurements to a COMET measurements file.

        For a valid COMET measurements file, write the header first with the `print_header()` method.
        The measurements themselves must be written in a specific order: the GPS coordinates are always the first line
        of a measurement, followed by serving cell line (or two lines in case of EN-DC), then the neighbouring cells
        lines.

        It is recommended to use the "with" statement when instantiating this class to make sure that the measurements
        are saved to disc in case of errors.

        This class allows to write a single measurements file, to make a new file create a new instance of
        MeasurementsWriter

        NOTE: If two instances of MeasurementsWriter are made at the same minute,
        the second one will overwrite the first

        :param dir_path: The path to the directory where measurements file will be stored. Can be relative or absolute.
            (Files will be ordered in directories of the date they were created at, inside this path)
        :param filename_suffix: A suffix added to the filename to distinguish the measurements files.
            Actual file name will have the following format: "hour-minute_suffix.csv".
        :param is_tmp: If True, filename will be prefixed with "tmp_".
        :param operator_info: An instance of COPS class containing the information about the mobile operator.
        """
        now = datetime.now()
        date_dir = now.strftime("%Y-%m-%d")
        file_prefix = now.strftime("%H-%M_")

        self.operator_info: COPS = operator_info

        if not dir_path.endswith("/"):
            dir_path += "/"

        self.dir_path: str = os.path.abspath(dir_path + date_dir + "/") + "/"
        self.filename: str = file_prefix + filename_suffix + ".csv"
        self.is_tmp: bool = is_tmp

        self.file: TextIOWrapper | None = None
        self.measurements_counter: int = 0
        """Counter of current measurement"""
        self.sync_period: int = 30
        """Indicates how often measurements must be synced with disc (in number of writes)"""

    def __enter__(self):
        """
        Creates a file in the specified directory (which is created if it doesn't exist) on "with" statement
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        """
        Closes the file when the "with" statement is exited (normally or because of an exception).
        
        The exception parameters are ignored, exceptions will be reported in a normal way.
        """
        if self.file:
            self.file.close()

    def open(self):
        """
        Open a file in writing mode at path given by `dir_path` and `filename` attributes. This will create
        intermediary directories if needed and will overwrite a file with the same name if it already exists.

        The file is opened with a line by line buffering. This means that each write is 3-4 times slower (which is still
        less than 100 microseconds) but ensures that every single measurement will be saved even on sudden shutdown
        """
        if not os.path.isdir(self.dir_path):
            os.makedirs(self.dir_path)

        if self.is_tmp:
            self.file = open(self.dir_path + "tmp_" + self.filename, "w", buffering=1)
        else:
            self.file = open(self.dir_path + self.filename, "w", buffering=1)

    def close(self):
        """
        Close the file access. This method must be called to assure that the file is properly written to disc. 
        """
        if self.file:
            self.file.close()

    def __write(self, text: str = ""):
        """
        Write text to the measurements file.

        Every `self.sync_period` measurement will sync the file with disc to prevent losing data in case of
        power failure. This sync can take up to around 10ms, which is why it's only done periodically.
        
        :param text: text to write to file
        """
        self.file.write(text)
        # Syncing with disc can take up to 10ms, so it is only done every self.sync_period measurements
        if self.measurements_counter % self.sync_period == 0:
            os.fsync(self.file.fileno())

    def __write_line(self, text: str = ""):
        """
        Write a line of text to the measurements file. This will add a linebreak to the written text
        
        :param text: string to write to file
        """
        self.__write(text + "\n")

    def get_file_path(self) -> str:
        """
        Returns path to the measurements file
        """
        if self.is_tmp:
            return self.dir_path + "tmp_" + self.filename
        else:
            return self.dir_path + self.filename

    def print_header(self):
        """
        Write the header to the measurements file
        """
        # self.write_line("TECHNO|" + self.operator_info.act.name)
        operator_name = "Unknown"
        if self.operator_info is not None:
            operator_name = self.operator_info.operator_name
        header = ("HEADER\n"
                  "VERSION|1.0\n"
                  f"DATE|{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
                  f"OPERATOR|{operator_name}\n"
                  "GPS_LOST|\n"
                  "COMMENT|\n"
                  "GPS|TIMESTAMP|LATITUDE|LONGITUDE\n"
                  "MEASURE_SERVING|TIMESTAMP|NETWORK_TYPE|TAC|CELLID|MCC|MNC|PCID|EARFCN|RSRQ|RSRP|RSSI|SINR|IS_EN_DC\n"
                  "MEASURE_NEIGHBOUR_INTRA|TIMESTAMP|NETWORK_TYPE|PCID|EARFCN|RSRQ|RSRP|RSSI\n"
                  "MEASURE_NEIGHBOUR_INTER|TIMESTAMP|NETWORK_TYPE|PCID|EARFCN|RSRQ|RSRP|RSSI\n"
                  "\n"
                  "MEASUREMENTS\n")
        self.__write(header)

    def print_gps_measurement(self, gps_info: CGPSINFO):
        """
        Write the GPS line to the measurements file depending on `gps_info` content.

        This will print an empty GPS entry when no position is found.
    
        :param gps_info: an instance of CGPSINFO class filled with localisation measurements.
        """
        self.measurements_counter += 1
        self.__write_line(gps_info.to_printable_string())

    def print_serving_cell_measurement(self, cell: QENGServing):
        """
        Write the MEASURE_SERVING line to the measurements file depending on `cell` content.
        
        This will print an empty MEASURE_SERVING entry when cell is in 3G or not registered on network

        :param cell: an instance of QENGServing class filled with measurements from the serving cell.
        """
        self.measurements_counter += 1
        self.__write_line(cell.to_printable_string())

    def print_neighbour_cell_measurement(self, cell: QENGNeighbour):
        """
        Write the MEASURE_NEIGHBOUR_INTRA or MEASURE_NEIGHBOUR_INTER line to the measurements file
        depending on `cell` content.

        :param cell: an instance of QENGNeighbour class filled with measurements from a neighbouring cell.
        """
        self.measurements_counter += 1
        self.__write_line(cell.to_printable_string())

    @staticmethod
    def add_gps_lost_header(file_path: str, gps_lost: bool):
        """
        Add information about whether the GPS signal was lost during measurements 
        or not to the measurements file header.

        This will read the file at `file_path` and rewrite its content
        with a GPS_LOST entry in the header depending on `gps_lost` parameter (GPS_LOST|NO or GPS_LOST|YES).

        The file at `file_path` must be a measurement file produced by MeasurementsWriter and must at least contain
        the header

        :param file_path: absolute or relative path to the measurement file to modify
        :param gps_lost: if True then write GPS_LOST|YES to header, if False write GPS_LOST|NO
        """
        with open(file_path, "r") as file:
            lines = file.readlines()

        logger = logging.getLogger(__name__)
        logging.basicConfig(filename='./logs/comet.log', level=logging.DEBUG)

        if len(lines) < 10:
            logger.error(f"ERROR: Tried adding GPS lost entry to an empty or non-measurement file: {file_path}. "
                         f"Measurements file will not be modified")
            return

        with open(file_path, "w") as file:
            if gps_lost:
                lines[4] = "GPS_LOST|YES\n"
            else:
                lines[4] = "GPS_LOST|NO\n"

            file.writelines(lines)


if __name__ == '__main__':
    print("MeasurementsWriter module is not executable")
