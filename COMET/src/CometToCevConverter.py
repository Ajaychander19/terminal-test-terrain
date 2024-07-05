import os
import time
from datetime import datetime
from functools import wraps
from io import TextIOWrapper

OFFSET = 5  # actual column of the first earfcn column


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        wrapper.total_time += elapsed_time
        return result

    wrapper.total_time = 0
    return wrapper


def syntax_error(line: int, msg: str, fatal: bool = False):
    """Reports a syntax error at given line. If fatal parameter is True, raises an exception.

    :param fatal: if True, will raise a SyntaxError. If false, will print the error message to standard output
    :param line: line of the file where the error occurred
    :param msg: error message

    :raises RuntimeError: the corresponding syntax error
    """
    if fatal:
        raise SyntaxError(f'Error: line {str(line)}, {msg}')
    else:
        print(f'Error: line {str(line)}, {msg}')


def should_omit(line: str, line_index: int = 0) -> bool:
    """Returns True if the line must be omitted because of incorrect format, incorrect values or their absence.

    Will report a non-fatal error at the given line index if the line is in wrong format

    :param line_index: index of the line in the file, used for reporting errors
    :param line: a line of the COMET measurements file
    :return: True if line must be omitted, False if not
    """
    stripped_line = line.strip()
    values = stripped_line.split(sep="|")
    nb_values = len(values)

    if stripped_line.startswith("GPS"):
        if nb_values != 5:
            syntax_error(line_index, "MEASURE_GPS is in wrong format, measurement will be omitted", fatal=False)
            return True
        if values[2] == "":
            return True
        return False
    elif stripped_line.startswith("MEASURE_SERVING"):
        if nb_values < 12:
            syntax_error(line_index, "MEASURE_SERVING is in wrong format, measurement will be omitted", fatal=False)
            return True
        pcid = int(values[7])
        earfcn = int(values[8])
        if values[2] == "" or pcid == 0 or earfcn >= 4294967295:
            return True
        return False
    elif stripped_line.startswith("MEASURE_NEIGHBOUR_INTRA") or stripped_line.startswith("MEASURE_NEIGHBOUR_INTER"):
        if nb_values < 7:
            syntax_error(line_index, "MEASURE_NEIGHBOUR is in wrong format, measurement will be omitted", fatal=False)
            return True
        pcid = int(values[3])
        earfcn = int(values[4])
        if values[2] == "" or pcid == 0 or earfcn >= 4294967295:
            return True
        return False

    return True


def get_operator_from_measurements(measurements_file_path: str) -> str:
    """Parse the beginning of the COMET measurements file to retrieve operator name
    and transform it into a usable format ("F SFR" becomes "SFR")

    :param measurements_file_path: Path to a measurements file produced by COMET
    :return: operator name or empty string if the operator name is not found or is not recognized
    """
    with open(measurements_file_path, "r") as measurements_file:
        for i, line in enumerate(measurements_file):
            stripped_line = line.strip()  # May be excessive but it's better just in case
            if stripped_line.startswith('MEASUREMENTS'):
                syntax_error(i, "No 'OPERATOR' line found in header", fatal=True)
                break
            if stripped_line.startswith('OPERATOR'):
                values = stripped_line.split('|')
                if len(values) < 2:
                    syntax_error(i, "No 'OPERATOR' was given in the measurement file", fatal=True)
                    return ""

                if "SFR" in values[1].upper():
                    return "SFR"
                elif "ORANGE" in values[1].upper():
                    return "ORANGE"
                elif "FREE" in values[1].upper():
                    return "FREE"
                elif "BOUYGUES" in values[1].upper():
                    return "BOUYGUES"
                else:
                    syntax_error(i, "Operator '" + values[1] + "' is not recognized in "
                                                               "current version of the converter", fatal=True)
                return ""
    return ""


def get_earfcns_pcis(measurements_file_path: str) -> dict[(int, int), int]:
    """Parse the COMET measurement file and retrieve a dictionary of sorted couples (earfcn, pci) associated to their
    frequency in measurements.

    :param measurements_file_path: Path to a measurements file produced by COMET
    :return: dictionary of unique ordered couples of (earfcn, pci) associated to the number of their appearance
        in measurements format: {(earfcn: int, pci: int): frequency: int}
    """
    earfcns: dict[int, list[int]] = dict()
    sorted_earfcns_pcis: list[(int, int)] = list()
    with open(measurements_file_path, "r") as measurements_file:
        passed_header = False
        ignore_measurement = False
        for line in measurements_file:
            # Ignore header
            if not passed_header:
                if line.startswith('MEASUREMENTS'):
                    passed_header = True
                continue

            # If the line must be omitted, ignore the entire measurement
            if should_omit(line):
                ignore_measurement = True
                continue
            # New measurement starts with GPS
            if line.startswith('GPS'):
                ignore_measurement = False
                continue
            if ignore_measurement:
                continue

            if line.startswith('MEASURE_SERVING'):
                parts = line.strip().split('|')
                pci = int(parts[7])
                earfcn = int(parts[8])
            elif line.startswith('MEASURE_NEIGHBOUR_INTRA') or line.startswith('MEASURE_NEIGHBOUR_INTER'):
                parts = line.strip().split('|')
                pci = int(parts[3])
                earfcn = int(parts[4])
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


class CometToCevConverter:
    def __init__(self, measurements_file_path: str, output_dir: str = "../cev/", filename: str = "M1"):
        """
        Takes a COMET measurement file and creates a CORENTIN compatible cev.csv file with processed measurements.
        The constructor only creates the file, to process measurements the process() method must be called

        :param measurements_file_path: Path to the COMET measurements file
        :param output_dir: Path to the directory where output file will be stored
        :param filename: an additional name to the file (will be prefixed with cev and date, can be empty)
        """

        self.columns: dict[(int, int), int] = dict()
        """Indexes of columns associated to each couple in following format: {(earfcn, pci): column_index}"""
        self.measurements_file_path = os.path.abspath(measurements_file_path)
        """Path to the COMET measurements file"""
        self.operator_name = get_operator_from_measurements(self.measurements_file_path)
        """Name of the mobile network operator extracted from the measurements file"""

        if self.operator_name == "":
            raise RuntimeError("Couldn't find the operator name")

        _output_dir = output_dir
        if not _output_dir.endswith("/"):
            _output_dir += "/"

        now = datetime.now()
        dir_date = now.strftime("%d-%m-%Y")
        file_date = now.strftime("%Y%m%d_%H%M")

        self.output_dir_path: str = os.path.abspath(_output_dir + dir_date) + "/"
        self.output_filename: str = "cev" + self.operator_name + "_" + file_date + "-" + filename + ".csv"

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
        if not os.path.isdir(self.output_dir_path):
            os.makedirs(self.output_dir_path)

        self.file = open(self.output_dir_path + self.output_filename, "w")

    def close(self):
        """
        Close the file and erase saved file content from memory
        """
        if self.file:
            self.file.close()

    def write(self, text: str):
        self.file.write(text)

    def process(self):
        """
        Convert the COMET measurement file to a CORENTIN compatible cev.csv file.
        This will parse the measurement file twice and write the converted measurements to the cev file.

        On very large files this might take a few seconds
        """
        before = datetime.now()
        self.print_header()
        print(f"It took {(datetime.now() - before).total_seconds()} to print the header")
        before = datetime.now()
        self.print_measurements()
        print(f"It took {(datetime.now() - before).total_seconds()} to print the measurements")

        print(f"Total time taken by write_measurement_line: {self.write_measurement_line.total_time:.4f} seconds")
        print(f"Total time taken by convert_serving: {self.write_serving_cell_lines.total_time:.4f} seconds")

    def print_header(self):
        """
        Write the header of a measurements file in the CORENTIN cev format, including all the couples of (earfcn, pci).

        This method also updates the columns attribute used in print_measurements() method.
        """
        # Parse measurements file to get earfcn and pci data
        earfcn_pci_couples_freq = get_earfcns_pcis(self.measurements_file_path)
        nb_couples = len(earfcn_pci_couples_freq)
        # Hashed dictionary to rapidly find the columns index associated to a couple (earfcn, pci).
        # Columns associate the actual column index to the (earfcn, pci) couple column
        self.columns = {couple: OFFSET + index for index, couple in enumerate(earfcn_pci_couples_freq)}
        if self.columns == {}:  # TODO: actually ask if there is a point of writing cells with no associated measurement
            raise RuntimeError("No valid cells found")

        self.write("DEFINE\nVERSION|Version\nDATE|Date\nTECHNO|Techno\n")

        earfcn_header_line = "|".join(f"EARFCN_{i}" for i in range(nb_couples))
        self.write(f"MEAS_EARFCNS|NA|NA|NA|NA|{earfcn_header_line}\n")

        pcis_header_line = "|".join(f"PCI_{i}" for i in range(nb_couples))
        self.write(f"MEAS_PCIS|NA|NA|NA|NA|{pcis_header_line}\n")

        beams_header_line = "|".join(f"BEAM_{i}" for i in range(nb_couples))
        self.write(f"MEAS_BEAMS|NA|NA|NA|NA|{beams_header_line}\n")

        meas_nb_header_line = "|".join(f"nb_meas_{i}" for i in range(nb_couples))
        self.write(f"MEAS_NB|NA|NA|NA|NA|{meas_nb_header_line}\n")

        self.write("CELLINFO|Timestamp|Lat|Lng|EARFCN|PCI|TAC|CID|MCC|MNC\n"
                   "MEASURE_SERVING|Timestamp|Lat|Lng|Serving_EARFCN|Serving_PCI|Serving_RSRP|Serving_RSRQ"
                   "|Serving_RSSI|Serving_CINR\n"
                   "MEASUREMENT|Timestamp|Lat|Lng|Measurement_Name|Values\n"
                   "CONTENT\n"
                   "VERSION|2.0\n"
                   f"DATE|{datetime.now().strftime("%d-%m-%Y %H:%M")}\n"
                   "TECHNO|4G\n",  # Only 4G measurements in COMET as it can't see neighbour cells in 5G mode
                   )

        # Write all earfcn found in ascending order
        earfcn_line = "|".join(str(earfcn_pci[0]) for earfcn_pci in earfcn_pci_couples_freq.keys())
        self.write(f"MEAS_EARFCNS|||||{earfcn_line}\n")

        # Write all PCIs found in ascending order
        pcis_line = "|".join(str(earfcn_pci[1]) for earfcn_pci in earfcn_pci_couples_freq.keys())
        self.write(f"MEAS_PCIS|||||{pcis_line}\n")

        # 0 is assigned to all couples because beams aren't used in 4G
        beams_line = "|".join("0" for _ in range(nb_couples))
        self.write(f"MEAS_BEAMS|||||{beams_line}\n")

        # Write frequencies of each couple
        # I need to try it with a for values
        meas_nb_line = "|".join(str(frequency) for _, frequency in earfcn_pci_couples_freq.items())
        self.write(f"MEAS_NB|||||{meas_nb_line}\n")

    def print_measurements(self):
        """
        Parse COMET measurements file line by line to extract measurements data and write it in the CORENTIN compatible
        format (writes CELLINFO, MEASURE_SERVING and MEASUREMENTS entries)

        This method must be called after print_header() updates the columns attribute
        """
        if self.columns == {}:
            raise RuntimeError("print_measurements() method can only be called after print_header()")

        with open(self.measurements_file_path, "r") as measurements_file:
            # Since coordinates are copied directly to output file with no change they can be kept as str
            coordinates = ("", "")
            current_measure_index = 0  # TODO: Check if a timestamp with "holes" in it will work
            current_measure = dict()  # {(earfcn, pci): (rsrp, rsrq, rssi)}
            passed_header = False
            ignore_measurement = False

            for line in measurements_file:
                stripped_line = line.strip()
                # Ignore header
                if not passed_header:
                    if stripped_line.startswith('MEASUREMENTS'):
                        passed_header = True
                    continue

                # If the line must be omitted, ignore the entire measurement
                if should_omit(line):
                    ignore_measurement = True
                    continue

                values = [value.strip() for value in stripped_line.split('|')]
                if stripped_line.startswith("GPS"):
                    coordinates = (values[2], values[3])
                    if coordinates[0] == '' or coordinates[1] == '':
                        ignore_measurement = True
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
                    # In EN-DC mode there will be 2 lines of MEASURE_SERVING. We're only interested in the LTE one here.
                    if values[2] != "LTE":
                        continue
                    self.write_serving_cell_lines(coordinates, current_measure_index, values)
                elif stripped_line.startswith("MEASURE_NEIGHBOUR_INTRA"):
                    if ignore_measurement:
                        continue
                    current_measure[(int(values[4]), int(values[3]))] = (values[6], values[5], values[7])
                elif stripped_line.startswith("MEASURE_NEIGHBOUR_INTER"):
                    if ignore_measurement:
                        continue
                    current_measure[(int(values[4]), int(values[3]))] = (values[6], values[5], values[7])

    @measure_time
    def write_serving_cell_lines(self, coordinates, current_measure_index, values):
        cell_info = (f"MEASURE_SERVING|{str(current_measure_index)}|"
                     f"{coordinates[0]}|{coordinates[1]}|"  # lat|lng
                     f"{values[8]}|{values[7]}|"  # earfcn|pci|
                     f"{values[10]}|{values[9]}|{values[11]}|{values[12]}"
                     f"\n")

        serving_info = (
            f"CELLINFO|{str(current_measure_index)}|{coordinates[0]}|{coordinates[1]}|"
            f"{values[8]}|{values[7]}|"
            f"{str(int(values[3], 16))}|{values[4]}|{values[5]}|{values[6]}"
            f"\n")

        self.write(cell_info)
        self.write(serving_info)

    @measure_time
    def write_measurement_line(self, coordinates: (str, str), current_measure: dict, current_measure_index,
                               meas_type: str):
        """

        :param coordinates: couple (lat: str, long: str) with coordinates of the measurement
        :param current_measure:
        :param current_measure_index:
        :param meas_type: "RSRP" or "RSRQ" or "RSSI"
        """
        if meas_type == "RSRP":
            i = 0
        elif meas_type == "RSRQ":
            i = 1
        elif meas_type == "RSSI":
            i = 2
        else:
            raise RuntimeError("MEASUREMENT line doesn't accept " + meas_type)

        # couples must be ordered in the same way as the header couples
        sorted_index_meas = list()
        for couple, meas in current_measure.items():
            sorted_index_meas.append((self.columns[couple], meas))
        sorted_index_meas = sorted(sorted_index_meas)
        current_column = OFFSET

        # Using a list join instead of string concatenation is slightly faster
        res_parts = ["MEASUREMENT|", str(current_measure_index), "|", coordinates[0], "|", coordinates[1], "|",
                     meas_type]

        for (index, meas) in sorted_index_meas:
            if index != current_column:
                res_parts.append("".join(["|"] * (index - current_column)))
                current_column = index
            res_parts.append("|" + str(meas[i]))
            current_column += 1

        # add empty cases at the end to match the number of columns
        last_column = len(self.columns) + OFFSET
        res_parts.append("".join(["|"] * (last_column - current_column)))

        res = "".join(res_parts)
        self.write(res + "\n")


if __name__ == '__main__':
    with CometToCevConverter("../measurements/05-07-2024/tmp_13-54_measurement.csv") as writer:
        writer.process()
