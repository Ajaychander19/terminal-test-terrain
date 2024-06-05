import os
from io import TextIOWrapper
from datetime import datetime
from ATResponses import COPS


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
    def __init__(self, data_dir: str, filename: str, is_tmp: bool):
        self.dir_path: str = data_dir
        self.filename: str = filename
        self.is_tmp: bool = is_tmp
        self.file: TextIOWrapper | None = None

    def __enter__(self):
        if not os.path.isdir(self.dir_path):
            os.mkdir(self.dir_path)

        if self.is_tmp:
            self.file = open(self.dir_path + "tmp_" + self.filename, "w")
        else:
            self.file = open(self.dir_path + self.filename, "w")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()

    def write(self, line: str = ""):
        self.file.write(line)

    def write_line(self, line: str = ""):
        self.file.write(line + "\n")


class MeasurementsWriter(Writer):
    def __init__(self, data_dir: str = "./measurements/", filename: str = "measurement.csv", is_tmp: bool = False,
                 operator_info: COPS = None):
        now = datetime.now()

        date_dir = now.strftime("%d-%m-%Y")
        file_prefix = now.strftime("%H-%M_")
        super().__init__(data_dir + date_dir + "/", file_prefix + filename, is_tmp)
        self.operator_info = operator_info

    def print_header(self):
        self.write_line("HEADER")
        self.write_line("VERSION|1.0")
        self.write_line("DATE|" + datetime.now().strftime("%d-%m-%Y %H:%M"))
        self.write_line("OPERATOR|" + self.operator_info.oper)
        # self.write_line("TECHNO|" + self.operator_info.act.name)
        self.write_line("GPS|TIMESTAMP|LATITUDE|LONGITUDE|ALTITUDE")
        self.write_line("MEASURE_SERVING|TIMESTAMP|NETWORK_TYPE|TAC|CELLID|MCC|MNC|PCID|EARFCN|RSRQ|RSRP|RSSI|SINR")
        self.write_line("MEASURE_NEIGHBOUR_INTRA|TIMESTAMP|NETWORK_TYPE|PCID|EARFCN|RSRQ|RSRP|RSSI|SINR")
        self.write_line("MEASURE_NEIGHBOUR_INTER|TIMESTAMP|NETWORK_TYPE|PCID|EARFCN|RSRQ|RSRP|RSSI|SINR")
        self.write_line()
        self.write_line("MEASUREMENTS")


class ProcessedFileWriter(Writer):
    def __init__(self, measurements_file_path: str, output_dir: str = "./data/", filename: str = "M1",
                 is_tmp: bool = False):
        """
        Takes a COMET measurement file and create a CORENTIN compatible cev.csv file with processed measurements.
        The constructor only creates the file, to process measurements print_header() and print_measurements()
        methods must be called

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
        self.write_line("TECHNO|4G")

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
            coordinates = ("0", "0")
            current_measure_index = 0
            # {(earfcn, pci): (rsrp, rsrq, rssi)}
            current_measure = dict()
            passed_header = False
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
                    # GPS line delimits the start of a measurement. After finishing reading previous measurement
                    # (neighbours) we can print all rsrp, rsrq, rssi measurements for all cells at once
                    if current_measure:
                        self.write_measurement_line(coordinates, current_measure, current_measure_index, "RSRP")
                        self.write_measurement_line(coordinates, current_measure, current_measure_index, "RSRQ")
                        self.write_measurement_line(coordinates, current_measure, current_measure_index, "RSSI")
                    current_measure_index += 1

                elif stripped_line.startswith("MEASURE_SERVING"):
                    self.write("CELLINFO|" + str(current_measure_index) + "|" +
                               coordinates[0] + "|" + coordinates[1] + "|" +  # lat|lng
                               values[8] + "|" + values[7] + "|" +  # earfcn|pci|
                               values[3] + "|" + str(int(values[4], 16)) + "|" + values[5] + "|" + values[6]
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
                    current_measure[(int(values[4]), int(values[3]))] = (values[6], values[5], values[7])
                elif stripped_line.startswith("MEASURE_NEIGHBOUR_INTER"):
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

    with ProcessedFileWriter("//measurements/03-06-2024/tmp_10"
                             "-49_measurement.csv", is_tmp=False) as writer:
        writer.print_header()
        writer.print_measurements()
