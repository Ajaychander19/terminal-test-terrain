import logging
from datetime import datetime
from datetime import timedelta
from typing import Tuple, List


def print_to_logger_or_stdout(msg: str, logger: logging.Logger = None, severity_level: int = logging.INFO):
    """
    Prints a message to standard output or to the logger if given. This exists mainly to avoid repeating if else
    when logger existence is not known

    :param msg: Message to print
    :param logger: If not None, the message will be printed using the logger
    :param severity_level: Decides the level of logged message
    """
    if logger is not None:
        logger.log(msg=msg, level=severity_level)
    else:
        print(msg)


def error_to_logger_or_raise(msg: str, logger: logging.Logger = None,
                             severity_level: int = logging.CRITICAL):
    """
    Print an error to the logger or raise a RuntimeError with given message if logger is not given

    :param msg: Message to print in logger or exception
    :param logger: If not None, the error message will be printed to the logger
    :param severity_level: Decides the level of logged message, CRITICAL by default, only used if logger is given
    """
    if logger is not None:
        logger.log(msg=msg, level=severity_level)
    else:
        raise RuntimeError(msg)


def split_comet_line(line: str) -> List[str]:
    """
    Splits a COMET measurements file path into parts
    :param line: A line from a COMET measurements file
    :return: a list of parts separated by the '|' in the line
    """
    return line.split("|")


def get_comet_timestamp(parts: List[str]) -> datetime:
    """
    Extract the timestamps from the parts of a COMET measurements file line into a Python datetime
    :param parts: A COMET measurements file line separated in parts
    :return: datetime of the timestamp
    """
    return datetime.strptime(parts[1], "%Y-%m-%d %H:%M:%S")


def check_no_gps_or_network_periods(comet_file_path: str):
    """
    Parse a COMET measurements file and print each period of measurements where no GPS or no network was available

    :param comet_file_path: Path to the measurements file
    """
    with open(comet_file_path, "r") as file:
        lines = file.readlines()

    passed_header = False

    no_gps_periods = []
    current_gps_start = None

    no_network_periods = []
    current_network_start = None

    gps_line_nb = 1
    network_line_nb = 1
    for i, line in enumerate(lines):

        # Ignore header
        if not passed_header:
            if line.startswith('MEASUREMENTS'):
                passed_header = True
            continue

        current_gps_start, no_gps_periods, gps_line_nb = (
            _process_gps_line(line, current_gps_start, no_gps_periods, gps_line_nb, i)
        )
        current_network_start, no_network_periods, network_line_nb = (
            _process_network_line(line, current_network_start, no_network_periods, network_line_nb, i)
        )

    # If the file ends while still in a no network period, record it
    if current_network_start is not None:
        no_network_periods.append((network_line_nb, current_network_start, lines[-1].split("|")[1]))

    # If the file ends while still in a no GPS period, record it
    if current_gps_start is not None:
        no_gps_periods.append((gps_line_nb, current_gps_start, lines[-1].split("|")[1]))

    # Calculate and display the duration of each no GPS period
    _display_no_gps_periods(no_gps_periods)

    # Calculate and display the duration of each no network period
    _display_no_network_periods(no_network_periods)


def _process_gps_line(line: str, period_start: datetime, no_gps_periods: list, period_start_line_nb: int,
                      current_line_nb: int) -> Tuple[datetime, list, int]:
    """
    Processes a GPS line and updates period_start, no_gps_periods, period_start_line_nb arguments.

    It sets period_start to the timestamp of the line if the period_start given was None (first line in the period).
    It will also update the period_start_line_nb with current_line_nb.

    If GPS is found again, uses the timestamp of the measurement as end of the no GPS period and returns
    no_gps_periods with the new period.

    :param line: line of the COMET measurements file
    :param period_start: timestamp of the start of the no GPS period
    :param no_gps_periods: list of periods with no GPS
    :param period_start_line_nb: Number of the line at which the no GPS period started
    :param current_line_nb: Number of the current line
    :return: Tuple with the updated (period_start, no_gps_periods, period_start_line_nb) arguments
    """
    if "GPS|" in line:
        parts = split_comet_line(line)
        timestamp = get_comet_timestamp(parts)
        latitude = parts[2]

        if latitude == "":  # No GPS signal
            if period_start is None:
                period_start = timestamp
                period_start_line_nb = current_line_nb
        else:  # GPS signal is available
            if period_start is not None:
                # End of a no GPS period
                no_gps_periods.append((period_start_line_nb, period_start, timestamp))
                period_start = None
    return period_start, no_gps_periods, period_start_line_nb


def _process_network_line(line: str, period_start: datetime, no_network_periods: list, period_start_line_nb: int,
                          current_line_nb: int) -> Tuple[datetime, list, int]:
    """
    Processes a MEASURE_SERVING line and updates period_start, no_network_periods, period_start_line_nb arguments.

    It sets period_start to the timestamp of the line if the period_start given was None (first line in the period).
    It will also update the period_start_line_nb with current_line_nb.

    If a network is found again, uses the timestamp of the measurement as end of the no network period and returns
    no_network_periods with the new period.

    :param line: line of the COMET measurements file
    :param period_start: timestamp of the start of the no network period
    :param no_network_periods: list of periods with no network
    :param period_start_line_nb: Number of the line at which the no network period started
    :param current_line_nb: Number of the current line
    :return: Tuple with the updated (period_start, no_network_periods, period_start_line_nb) arguments
    """
    if "MEASURE_SERVING|" in line:
        parts = split_comet_line(line)
        timestamp = get_comet_timestamp(parts)
        network_type = parts[2]

        if network_type == "":  # No network
            if period_start is None:  # Set the timestamp if it was not yet set
                period_start = timestamp
                period_start_line_nb = current_line_nb
        else:  # network is available
            if period_start is not None:
                # End of a no network period
                no_network_periods.append((period_start_line_nb, period_start, timestamp))
                period_start = None
    return period_start, no_network_periods, period_start_line_nb


def _display_no_network_periods(no_network_periods: List[Tuple[int, datetime, datetime]]):
    """
    Displays in the console all periods with no network in the given list
    :param no_network_periods: list of no network periods with the number of the first line, timestamp of start and
    timestamp of end
    """
    total_duration = timedelta(0)
    for i, start, end in no_network_periods:
        duration = end - start
        total_duration += duration
        print(f"No network from {start} to {end} lasting {duration} starting on line {str(i)}")
    # Display the number of no network periods
    print(f"Total number of no network periods: {len(no_network_periods)} ({total_duration} in total)")
    print("------------------------------------------------------\n")


def _display_no_gps_periods(no_gps_periods: List[Tuple[int, datetime, datetime]]):
    """
    Displays in the console all periods with no gps in the given list
    :param no_gps_periods: list of no gps periods with the number of the first line, timestamp of start and
    timestamp of end
    """
    total_duration = timedelta(0)
    for i, start, end in no_gps_periods:
        duration = end - start
        total_duration += duration
        print(f"No GPS from {start} to {end} lasting {duration} starting on line {str(i)}")
    # Display the number of no GPS periods
    print(f"Total number of no GPS periods: {len(no_gps_periods)} ({total_duration} in total)")
    print("------------------------------------------------------\n")


if __name__ == "__main__":
    check_no_gps_or_network_periods("/home/stepan-tyurin/Documents/terminal-test-terrain/COMET/saved_measurements/"
                                    "second_night_measurement/17-24_measurement.csv")
