"""
Requires Python 3.6 or newer (f-strings)
"""

import os
import time
from datetime import datetime
from functools import wraps
from io import TextIOWrapper

OFFSET = 5  # actual column of the first earfcn column


def measure_time(func):
    """A wrapper function that allows to see for how long the function was active

    Usage:
        >>> @measure_time
        >>> def dummy():
        >>>     pass
        >>> dummy()
        >>> print(f"Total time taken by func: {dummy.total_time:.4f} seconds")
    """

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

    Examples:
        >>> should_omit("GPS|2024||")
        >>> True
        >>> should_omit("MEASURE_SERVING|2024-06-11 15:16:14|LTE|0xC0FA|159130624|208|10|75|2825|-18.1|-109.0|-72.3|-4")
        >>> False
        >>> should_omit("MEASURE_SERVING|10|75|2825|-18.1|-109.0|-72.3|-4")
        >>> "MEASURE_SERVING is in wrong format, measurement will be omitted"
        >>> True

    :param line_index: index of the line in the file, used for reporting errors
    :param line: a line of the COMET measurements file
    :return: True if line must be omitted, False if not
    """
    stripped_line = line.strip()
    values = stripped_line.split(sep="|")
    nb_values = len(values)

    if stripped_line.startswith("GPS"):
        if nb_values != 4:
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
        # Ignore the non-LTE measurements in current version
        if values[2].strip() != "LTE" or pcid == 0 or earfcn >= 4294967295:
            return True
        return False
    elif stripped_line.startswith("MEASURE_NEIGHBOUR_INTRA") or stripped_line.startswith("MEASURE_NEIGHBOUR_INTER"):
        if nb_values < 7:
            syntax_error(line_index, "MEASURE_NEIGHBOUR is in wrong format, measurement will be omitted", fatal=False)
            return True
        pcid = int(values[3])
        earfcn = int(values[4])
        if values[2].strip() != "LTE" or pcid == 0 or earfcn >= 4294967295:
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
            stripped_line = line.strip()
            if stripped_line == "":  # Ignore empty lines
                continue
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
        previous_pci_earfcn = (0, 0)
        previous_serving = False
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
                previous_serving = False
                continue
            if ignore_measurement:
                continue

            if line.startswith('MEASURE_SERVING'):
                parts = line.strip().split('|')
                pci = int(parts[7])
                earfcn = int(parts[8])
                previous_serving = True
                previous_pci_earfcn = (pci, earfcn)
            elif line.startswith('MEASURE_NEIGHBOUR_INTRA') or line.startswith('MEASURE_NEIGHBOUR_INTER'):
                parts = line.strip().split('|')
                pci = int(parts[3])
                earfcn = int(parts[4])
                # If previous line was measure_serving,
                # and it had the same pci and earfcn, don't count it, it's the same cell
                if previous_serving and previous_pci_earfcn == (pci, earfcn):
                    previous_serving = False
                    continue
            else:
                previous_serving = False
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

        The measurement file must at least contain a valid header (including an operator name) and at least one
        valid measurement, an exception will be raised if it's not the case.

        Example:
            >>> with CometToCevConverter("../measurements/11-06-2024/tmp_15-16_measurement.csv") as converter:
            >>>     converter.process()
            >>> with open("../cev/05-07-2024/cevSFR_20240705_1457-M1.csv") as file:
            >>>     print(file.read())

        :param measurements_file_path: Path to the COMET measurements file
        :param output_dir: Path to the directory where output file will be stored
        :param filename: an additional name to the file (will be prefixed with cev and date, can be empty)
        """

        self.current_measure: dict[(int, int), (int, int, int)] = dict()
        """The dictionary containing the network measurements for each cell of the current measurement"""
        self.columns: dict[(int, int), int] = dict()
        """Indexes of columns associated to each couple in following format: {(earfcn, pci): column_index}"""
        self.measurements_file_path = os.path.abspath(measurements_file_path)
        """Path to the COMET measurements file"""
        self.operator_name = get_operator_from_measurements(self.measurements_file_path)
        """Name of the mobile network operator extracted from the measurements file"""
        self.measurements_starting_timestamp: datetime = datetime(1970, 1, 1)
        """The starting datetime of the measurement session. 
        Must be extracted from the header or the first measurement"""

        if self.operator_name == "":
            raise RuntimeError("Couldn't find the operator name")

        _output_dir = output_dir
        if not _output_dir.endswith("/"):
            _output_dir += "/"

        now = datetime.now()
        dir_date = now.strftime("%d-%m-%Y")
        file_date = now.strftime("%Y%m%d_%H%M")

        self.output_dir_path: str = os.path.abspath(_output_dir + dir_date) + "/"
        """The absolute path to the output directory"""
        self.output_filename: str = "cev" + self.operator_name + "_" + file_date + "-" + filename + ".csv"
        """The output file name"""

        self.file: TextIOWrapper | None = None
        """Output file access"""

    def __enter__(self):
        """
        Creates a file in the specified directory (which is created if it doesn't exist) on "with" statement
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        """
        Closes the file when the "with" statement is exited (normally or because of an exception)

        The exception parameters are ignored, exceptions will be reported in a normal way.
        """
        self.close()

    def open(self):
        """Open the output file in write mode, creating the file and intermediary directories if needed"""
        if not os.path.isdir(self.output_dir_path):
            os.makedirs(self.output_dir_path)

        self.file = open(self.output_dir_path + self.output_filename, "w")

    def close(self):
        """Close the output file finishing writing to disc"""
        if self.file:
            self.file.close()

    def write(self, text: str):
        """Write a string to the output file

        :param text: Text to write to file
        """
        self.file.write(text)

    def process(self):
        """Convert the COMET measurement file to a CORENTIN compatible cev.csv file.
        This will parse the measurement file twice and write the converted measurements to the output cev file.

        Might take around a second on very large files
        """
        before = datetime.now()
        self.print_header()
        print(f"It took {(datetime.now() - before).total_seconds()} to print the header")
        before = datetime.now()
        self.print_measurements()
        print(f"It took {(datetime.now() - before).total_seconds()} to print the measurements")

        print(f"Total time taken by write_measurement_line: {self.write_measurement_line.total_time:.4f} seconds")
        print(f"Total time taken by write_serving_cell_lines: {self.write_serving_cell_lines.total_time:.4f} seconds")

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
        if self.columns == {}:
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

        # TODO: decide if it's better to use to date of measurement or the date of conversion
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

        # Write number of occurrences of each couple
        meas_nb_line = "|".join(str(frequency) for frequency in earfcn_pci_couples_freq.values())
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
            seconds_since_start: float = 0.0
            self.current_measure = dict()  # {(earfcn, pci): (rsrp, rsrq, rssi)}
            passed_header = False
            ignore_measurement = False

            for line in measurements_file:
                stripped_line = line.strip()
                if stripped_line == "":  # Ignore empty lines
                    continue

                # Find the starting date in the header, ignore the rest of it
                if not passed_header:
                    if stripped_line.startswith("DATE"):
                        values = [value.strip() for value in stripped_line.split('|')]
                        if len(values) != 2:
                            syntax_error(line=0, msg="No date found in the measurements file header "
                                                     "or the date line has wrong format", fatal=True)
                        self.measurements_starting_timestamp = datetime.strptime(values[1], '%d-%m-%Y %H:%M:%S')

                    if stripped_line.startswith('MEASUREMENTS'):
                        passed_header = True
                        if self.measurements_starting_timestamp == datetime(1970, 1, 1):
                            syntax_error(line=0, msg="No date found in the measurements file header", fatal=True)
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
                    self.write_measurements_lines(coordinates, seconds_since_start)

                    # Gives the "index" of the measurement in the measurement file, doesn't have to be continuous
                    seconds_since_start = (datetime.strptime(values[1], '%Y-%m-%d %H:%M:%S') -
                                           self.measurements_starting_timestamp).total_seconds()

                elif stripped_line.startswith("MEASURE_SERVING"):
                    if ignore_measurement:
                        continue
                    # In EN-DC mode there will be 2 lines of MEASURE_SERVING. We're only interested in the LTE one here.
                    if values[2] != "LTE":
                        continue
                    self.write_serving_cell_lines(coordinates, seconds_since_start, values)
                elif stripped_line.startswith("MEASURE_NEIGHBOUR_INTRA"):
                    if ignore_measurement:
                        continue
                    self.current_measure[(int(values[4]), int(values[3]))] = (values[6], values[5], values[7])
                elif stripped_line.startswith("MEASURE_NEIGHBOUR_INTER"):
                    if ignore_measurement:
                        continue
                    self.current_measure[(int(values[4]), int(values[3]))] = (values[6], values[5], values[7])

            # Write the last measurement
            self.write_measurements_lines(coordinates, seconds_since_start)

    def write_measurements_lines(self, coordinates, seconds_since_start):
        """Write the 3 MEASUREMENT line of the current measurement. This method will empty the current_measurement
        attribute to avoid keeping old measurements after they are written to file

        :param coordinates: couple (lat: str, long: str) with the GPS coordinates of the measurement
        :param seconds_since_start: Number of seconds elapsed since the start of the measurement session
        """
        if self.current_measure:
            self.write_measurement_line(coordinates, seconds_since_start, "RSRP")
            self.write_measurement_line(coordinates, seconds_since_start, "RSRQ")
            self.write_measurement_line(coordinates, seconds_since_start, "RSSI")
            self.current_measure = dict()  # Empty dict to avoid keeping old measurements

    @measure_time
    def write_serving_cell_lines(self, coordinates: (str, str), seconds_since_start: float, values: list):
        """Write to the output file the MEASURE_SERVING and CELLINFO lines

        :param coordinates: couple (lat: str, long: str) with the GPS coordinates of the measurement
        :param seconds_since_start: Number of seconds elapsed since the start of the measurement session
        :param values: The values extracted from the MEASURE_SERVING line of the measurements file
        """
        serving_info = (f"MEASURE_SERVING|{str(seconds_since_start)}|"
                        f"{coordinates[0]}|{coordinates[1]}|"  # lat|lng
                        f"{values[8]}|{values[7]}|"  # earfcn|pci|
                        f"{values[10]}|{values[9]}|{values[11]}|{values[12]}"
                        f"\n")

        cell_info = (
            f"CELLINFO|{str(seconds_since_start)}|{coordinates[0]}|{coordinates[1]}|"
            f"{values[8]}|{values[7]}|"
            f"{str(int(values[3], 16))}|{values[4]}|{values[5]}|{values[6]}"
            f"\n")

        self.write(cell_info)
        self.write(serving_info)

    @measure_time
    def write_measurement_line(self, coordinates: (str, str),
                               seconds_since_start: float, meas_type: str):
        """Write a MEASUREMENT line to the output file with the RSRP, RSRQ or RSSI or the current measurement
        depending on the meas_type parameter

        :param coordinates: couple (lat: str, long: str) with coordinates of the measurement
        :param seconds_since_start: Number of seconds elapsed since the start of the measurement session
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
        for couple, meas in self.current_measure.items():
            sorted_index_meas.append((self.columns[couple], meas))
        sorted_index_meas = sorted(sorted_index_meas)
        current_column = OFFSET

        # Using a list join instead of string concatenation is slightly faster
        res_parts = ["MEASUREMENT|", str(seconds_since_start), "|", coordinates[0], "|", coordinates[1], "|",
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
    # with CometToCevConverter("../measurements/11-06-2024/tmp_15-16_measurement.csv") as writer:
    #     writer.process()
    # with CometToCevConverter("../measurements/10-07-2024/tmp_14-35_measurement.csv") as writer:
    #     writer.process()

    with CometToCevConverter("../measurements/11-07-2024/tmp_16-27_measurement.csv") as writer:
        writer.process()
