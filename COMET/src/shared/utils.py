import logging
from datetime import datetime
from datetime import timedelta


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


# TODO: refactor this, it's ugly
def check_no_gps_or_network_periods(file_path: str):
    """
    Parse a COMET measurements file and print each period of measurements where no GPS or no network was available

    :param file_path: Path to the measurements file
    """
    with open(file_path, "r") as file:
        lines = file.readlines()

    no_gps_periods = []
    current_gps_start = None

    no_network_periods = []
    current_network_start = None

    gps_line_nb = 1
    network_line_nb = 1
    for i, line in enumerate(lines):
        if "GPS|" in line:
            parts = line.split("|")
            timestamp = parts[1]
            gps_data = parts[2]

            if gps_data == "":  # No GPS signal
                if current_gps_start is None:
                    gps_line_nb = i + 1
                    current_gps_start = timestamp
            else:  # GPS signal is available
                if current_gps_start is not None:
                    # End of a no GPS period
                    no_gps_periods.append((gps_line_nb, current_gps_start, timestamp))
                    current_gps_start = None

        if "MEASURE_SERVING|" in line:
            parts = line.split("|")
            timestamp = parts[1]
            network_type = parts[2]

            if network_type == "":  # No network
                if current_network_start is None:
                    network_line_nb = i + 1
                    current_network_start = timestamp
            else:  # network is available
                if current_network_start is not None:
                    # End of a no network period
                    no_network_periods.append((network_line_nb, current_network_start, timestamp))
                    current_network_start = None

    # If the file ends while still in a no network period, record it
    if current_network_start is not None:
        no_network_periods.append((network_line_nb, current_network_start, lines[-1].split("|")[1]))

    # If the file ends while still in a no GPS period, record it
    if current_gps_start is not None:
        no_gps_periods.append((gps_line_nb, current_gps_start, lines[-1].split("|")[1]))

    # Calculate and display the duration of each no GPS period
    total_duration = timedelta(0)
    for i, start, end in no_gps_periods:
        start_time = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        duration = end_time - start_time
        total_duration += duration
        print(f"No GPS from {start} to {end} lasting {duration} starting on line {str(i)}")

    # Display the number of no GPS periods
    print(f"Total number of no GPS periods: {len(no_gps_periods)} ({total_duration} in total)")
    print("------------------------------------------------------\n")

    # Calculate and display the duration of each no network period
    total_duration = timedelta(0)
    for i, start, end in no_network_periods:
        start_time = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        duration = end_time - start_time
        total_duration += duration
        print(f"No network from {start} to {end} lasting {duration} starting on line {str(i)}")

    # Display the number of no network periods
    print(f"Total number of no network periods: {len(no_network_periods)} ({total_duration} in total)")
    print("------------------------------------------------------\n")


if __name__ == "__main__":
    check_no_gps_or_network_periods("/home/stepan-tyurin/Documents/terminal-test-terrain/COMET/saved_measurements/"
                                    "second_night_measurement/17-24_measurement.csv")
