import os
from io import TextIOWrapper
from datetime import datetime

from ATResponses import COPS


def syntax_error(line: int, msg: str):
    """Raises a syntax error.

    Parameters:
        line: line of the file where the error occurred.
        msg: error message.

    Raises:
        RuntimeError: the corresponding syntax error.
    """
    raise RuntimeError(f'Error: line {str(line)}, {msg}')


def get_operator_from_measurements(measurements_file_path: str) -> str:
    """
    Parse the beginning of the COMET measurements file to retrieve operator name and transform it into a usable format
    ("F SFR" becomes "SFR")
    :param measurements_file_path: Path to a measurements file produced by COMET
    :return: operator name or empty string if file format is incorrect (couldn't find OPERATOR line)
    """
    with open(measurements_file_path, "r") as measurements_file:
        for line in measurements_file:
            stripped_line = line.strip()  # May be excessive but it's better just in case
            if stripped_line.startswith('MEASUREMENTS'):
                print("ERROR: No operator name in file")
                break
            if stripped_line.startswith('OPERATOR'):
                values = stripped_line.split('|')
                if "SFR" in values[1]:
                    return "SFR"
                if "ORANGE" in values[1]:
                    return "ORANGE"
                if "FREE" in values[1]:
                    return "FREE"
                if "BOUYGUES" in values[1]:
                    return "BOUYGUES"
                return ""
    return ""


def get_earfcns_pcis(measurements_file_path: str):
    """

    :param measurements_file_path: Path to a measurements file produced by COMET
    :return: dictionary of unique ordered couples of (earfcn, pci) associated to the number of their appearance
    in measurements format: {(earfcn: int, pci: int): frequency: int}
    """
    # FIXME: It still counts the lines omitted because of lack of gps coordinates
    earfcns: dict[int, list[int]] = dict()
    sorted_earfcns_pcis: list[(int, int)] = list()
    with open(measurements_file_path, "r") as measurements_file:
        passed_header = False
        for line in measurements_file:
            # Ignore header
            if not passed_header:
                if line.startswith('MEASUREMENTS'):
                    passed_header = True
                continue

            earfcn = -1
            pci = -1
            if line.startswith('MEASURE_SERVING'):
                parts = line.strip().split('|')
                earfcn = int(parts[8])
                pci = int(parts[7])
            elif line.startswith('MEASURE_NEIGHBOUR_INTRA') or line.startswith('MEASURE_NEIGHBOUR_INTER'):
                parts = line.strip().split('|')
                earfcn = int(parts[4])
                pci = int(parts[3])
            else:
                continue

            # Keep duplicates with a list to calculate frequency later
            if earfcn not in earfcns.keys():
                earfcns[earfcn] = [pci]
            else:
                earfcns[earfcn].append(pci)

        # Sort pcis of each earfcn. Here the set of pcis is transformed into a sorted list of pcis
        for earfcn in earfcns:
            earfcns[earfcn] = sorted(earfcns[earfcn])

        # Sort all earfcn and create sorted couples
        for earfcn in sorted(earfcns):
            for pci in earfcns[earfcn]:
                sorted_earfcns_pcis.append((earfcn, pci))

        # Remove duplicates and associate a frequency to each couple
        frequencies: dict[(int, int), int] = dict()
        for couple in sorted_earfcns_pcis:
            if couple not in frequencies:
                frequencies[couple] = 1
            else:
                frequencies[couple] += 1
        # Python dictionary is insertion-ordered so no need to sort it again
    return frequencies


class Writer:
    """
    Base class for writing text to a file in the specified directory with specified filename.

    Must be used with a "with" statement, if it isn't, file must be opened manually
    (writer.file = open(writer.dir_path + writer.filename, "w")
    """
    def __init__(self, dir_path: str, filename: str, is_tmp: bool):
        self.dir_path: str = dir_path
        self.filename: str = filename
        self.is_tmp: bool = is_tmp
        self.file_content: str = ""
        self.file: TextIOWrapper | None = None

    def __enter__(self):
        """
        Creates a file in the specified directory (which is created if doesn't exist) on "with" statement
        """
        if not os.path.isdir(self.dir_path):
            os.mkdir(self.dir_path)

        if self.is_tmp:
            self.file = open(self.dir_path + "tmp_" + self.filename, "w")
        else:
            self.file = open(self.dir_path + self.filename, "w")
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        """
        Closes the file when the "with" statement is exited (normally or because of an exception)
        :param exc_type:
        :param exc_val:
        :param traceback:
        :return:
        """
        if self.file:
            self.file.close()

    def write(self, text: str = ""):
        self.file.write(text)
        self.file_content += text

    def write_line(self, line: str = ""):
        self.file.write(line + "\n")
        self.file_content += (line + "\n")

    def get_file_path(self) -> str:
        if self.is_tmp:
            return self.dir_path + "tmp_" + self.filename
        else:
            return self.dir_path + self.filename


class MeasurementsWriter(Writer):
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
        super().__init__(dir_path + date_dir + "/", file_prefix + filename, is_tmp)
        self.operator_info: COPS = operator_info

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

    @staticmethod
    def add_gps_lost_header(file_path: str, file_content: list[str], gps_lost: bool):
        """
        Add information about whether the GPS signal was lost during measurements or not to the measurement file header.

        This will rewrite the file at `file_path` with lines of text given by `file_content`,
        while adding YES or NO to the GPS_LOST entry in the header depending on `gps_lost` parameter

        This function rewrites the entire file and can take fairly long time to write on big files.
        For example on a file with 1 hour of measurements it could take around 100ms or more.

        :param file_path: absolute or relative path to the measurement file
        :param file_content: Old content of the measurement file in form of list of lines. It must contain a header and
        the measurements that were taken. Each line must end with a line break.
        :param gps_lost: if True then write GPS_LOST|YES to header, if False write GPS_LOST|NO
        """
        with open(file_path, "w") as file:
            # Ideally it would simply read the content of the file before writing but at that point its content is not
            # yet available
            lines = file_content
            if len(lines) < 10:
                print(f"ERROR: Tried adding GPS lost entry to an empty or non-measurement file: {file_path}")
                return
            if gps_lost:
                lines[4] = "GPS_LOST|YES\n"
            else:
                lines[4] = "GPS_LOST|NO\n"

            file.writelines(lines)


# TODO: Add error handling
class ProcessedFileWriter(Writer):
    def __init__(self, measurements_file_path: str, output_dir: str = "./data/", filename: str = "M1",
                 is_tmp: bool = False):
        """
        Takes a COMET measurement file and creates a CORENTIN compatible cev.csv file with processed measurements.
        The constructor only creates the file, to process measurements print_header() and print_measurements()
        methods must be called

        Note: This class must be instantiated using with statement as it doesn't provide a dedicated close() method

        :param measurements_file_path: Path to the COMET measurements file
        :param output_dir: Path to the directory where output file will be stored
        :param filename: an additional name to the file (will be prefixed with cev and date, can be empty)
        :param is_tmp: if True, output file name is prefixed with tmp_
        """
        now = datetime.now()
        dir_date = now.strftime("%d-%m-%Y")
        file_date = now.strftime("%Y%m%d_%H%M-")

        self.columns: dict[(int, int), int] = dict()
        """Indexes of columns associated to each couple in following format: {(earfcn, pci): column_index}"""
        self._measurements_file_path = measurements_file_path
        """Path to the COMET measurements file"""
        self._operator_name = get_operator_from_measurements(self._measurements_file_path)
        """Name of the mobile network operator extracted from the measurements file"""
        if self._operator_name == "":
            raise Exception("Incorrect measurements file format: couldn't find operator name")

        super().__init__(output_dir + dir_date + "/", "cev" + self._operator_name + "_" +
                         file_date + filename + ".csv", is_tmp)

    def print_header(self):
        """
        Writes the header of a measurements file in the CORENTIN cev format, including all the couples of (earfcn, pci).
        (stops just before the first measurement)
        This method also updates the columns attribute used in print_measurements() method.
        """
        self.write_line("DEFINE")
        self.write_line("VERSION|Version")
        self.write_line("DATE|Date")
        self.write_line("TECHNO|Techno")

        # Parse measurements file to get earfcn and pci data
        earfcn_pci_couples_freq = get_earfcns_pcis(self._measurements_file_path)
        offset = 5  # actual column of the first earfcn column
        # Hashed dictionary to rapidly find the columns index associated to a couple (earfcn, pci).
        self.columns = {couple: offset + index for index, couple in enumerate(earfcn_pci_couples_freq)}
        nb_couples = len(earfcn_pci_couples_freq)

        self.write("MEAS_EARFCNS|NA|NA|NA|NA")
        for i in range(nb_couples):
            self.write("|EARFCN_" + str(i))
        self.write_line()

        self.write("MEAS_PCIS|NA|NA|NA|NA")
        for i in range(nb_couples):
            self.write("|PCI_" + str(i))
        self.write_line()

        self.write("MEAS_BEAMS|NA|NA|NA|NA")
        for i in range(nb_couples):
            self.write("|BEAM_" + str(i))
        self.write_line()

        self.write("MEAS_NB|NA|NA|NA|NA")
        for i in range(nb_couples):
            self.write("|nb_meas_" + str(i))
        self.write_line()

        self.write_line("CELLINFO|Timestamp|Lat|Lng|EARFCN|PCI|TAC|CID|MCC|MNC")
        self.write_line("MEASURE_SERVING|Timestamp|Lat|Lng|Serving_EARFCN|Serving_PCI|Serving_RSRP|Serving_RSRQ"
                        "|Serving_RSSI|Serving_CINR")
        self.write_line("MEASUREMENT|Timestamp|Lat|Lng|Measurement_Name|Values")
        self.write_line("CONTENT")
        self.write_line("VERSION|2.0")
        self.write_line("DATE|" + datetime.now().strftime("%d-%m-%Y %H:%M"))
        self.write_line("TECHNO|4G")  # TODO: add 5G if possible with COMET

        self.write("MEAS_EARFCNS||||")
        for earfcn_pci in earfcn_pci_couples_freq.keys():
            self.write("|" + str(earfcn_pci[0]))
        self.write_line()

        self.write("MEAS_PCIS||||")
        for earfcn_pci in earfcn_pci_couples_freq.keys():
            self.write("|" + str(earfcn_pci[1]))
        self.write_line()

        self.write("MEAS_BEAMS||||")
        for i in range(nb_couples):
            self.write("|0")
        self.write_line()

        self.write("MEAS_NB||||")
        for _, frequency in earfcn_pci_couples_freq.items():
            self.write("|" + str(frequency))
        self.write_line()

    def print_measurements(self):
        """
        Reads COMET measurements file line by line to extract measurements data and write it in the CORENTIN compatible
        format (writes CELLINFO, MEASURE_SERVING and MEASUREMENTS entries)
        """
        if self.columns == {}:
            print("print_measurements() method can only be called after print_header()")
            return None

        with open(self._measurements_file_path, "r") as measurements_file:
            # Since coordinates are copied directly to output file with no change they can be kept as str
            coordinates = ("", "")
            current_measure_index = 0
            current_measure = dict()  # {(earfcn, pci): (rsrp, rsrq, rssi)}
            passed_header = False
            ignore_measurement = False
            for line in measurements_file:
                stripped_line = line.strip()
                # Ignore header
                if not passed_header:
                    if line.startswith('MEASUREMENTS'):
                        passed_header = True
                    continue

                values = [value.strip() for value in stripped_line.split('|')]
                if stripped_line.startswith("GPS"):
                    coordinates = (values[2], values[3])
                    if coordinates[0] == '' or coordinates[1] == '':
                        ignore_measurement = True
                        # current_measure_index += 1 # In theory it's the timestamp, so it should be incremented
                        continue
                    else:
                        ignore_measurement = False
                    # GPS line delimits the start of a measurement. After finishing reading previous measurement
                    # (neighbours) we can print all rsrp, rsrq, rssi measurements for all cells at once
                    if current_measure:
                        self.write_measurement_line(coordinates, current_measure, current_measure_index, "RSRP")
                        self.write_measurement_line(coordinates, current_measure, current_measure_index, "RSRQ")
                        self.write_measurement_line(coordinates, current_measure, current_measure_index, "RSSI")
                        current_measure = dict()  # Empty dict to avoid keeping old measurements
                    current_measure_index += 1

                elif stripped_line.startswith("MEASURE_SERVING"):
                    if ignore_measurement:
                        continue
                    self.write("CELLINFO|" + str(current_measure_index) + "|" +
                               coordinates[0] + "|" + coordinates[1] + "|" +  # lat|lng
                               values[8] + "|" + values[7] + "|" +  # earfcn|pci|
                               str(int(values[3], 16)) + "|" + values[4] + "|" + values[5] + "|" + values[6]
                               # TAC|CID|MCC|MNC
                               )
                    self.write_line()

                    self.write("MEASURE_SERVING|" + str(current_measure_index) + "|" +
                               coordinates[0] + "|" + coordinates[1] + "|" +  # lat|lng
                               values[8] + "|" + values[7] + "|" +  # earfcn|pci|
                               values[10] + "|" + values[9] + "|" + values[11] + "|" + values[12]  # RSRP|RSRQ|RSSI|CINR
                               )
                    self.write_line()
                elif stripped_line.startswith("MEASURE_NEIGHBOUR_INTRA"):
                    if ignore_measurement:
                        continue
                    current_measure[(int(values[4]), int(values[3]))] = (values[6], values[5], values[7])
                elif stripped_line.startswith("MEASURE_NEIGHBOUR_INTER"):
                    if ignore_measurement:
                        continue
                    current_measure[(int(values[4]), int(values[3]))] = (values[6], values[5], values[7])

    def write_measurement_line(self, coordinates, current_measure, current_measure_index, meas_type: str):
        """

        :param coordinates:
        :param current_measure:
        :param current_measure_index:
        :param meas_type: "RSRP" or "RSRQ" or "RSSI"
        :return:
        """
        if meas_type == "RSRP":
            i = 0
        elif meas_type == "RSRQ":
            i = 1
        elif meas_type == "RSSI":
            i = 2
        else:
            raise Exception("MEASUREMENT line doesn't accept " + meas_type)

        res = ""
        res += "MEASUREMENT|" + str(current_measure_index) + "|" + coordinates[0] + "|" + coordinates[1] + "|" +  meas_type

        # couples must be ordered in the same way as the header couples
        sorted_index_meas = list()
        for couple, meas in current_measure.items():
            sorted_index_meas.append((self.columns[couple], meas))
        sorted_index_meas = sorted(sorted_index_meas)
        current_column = 5
        for (index, meas) in sorted_index_meas:
            while index != current_column:
                res += "|"
                current_column += 1
            res += "|" + str(meas[i])
            current_column += 1
        self.write_line(res)


if __name__ == '__main__':
    print("FileWriters module isn't executable")
    # Get MiB taken by this process
    # import os, psutil; print(psutil.Process().memory_info().rss / 1024 ** 2)
    before = datetime.now()
    with ProcessedFileWriter("./measurements/11-06-2024/tmp_15"
                             "-16_measurement.csv", is_tmp=False) as writer:
        writer.print_header()
        writer.print_measurements()
    after = datetime.now()

    duration = after - before
    print(duration)
    duration_per_second = duration.total_seconds()/(40*60)
    print(duration_per_second)
    estimated_two_hour_duration = duration_per_second * (2*60*60)
    print(estimated_two_hour_duration)
