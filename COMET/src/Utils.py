import logging
from datetime import datetime


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


def check_no_gps_periods(file_path: str = "../measurements/11-07-2024/tmp_16-27_measurement.csv"):
    with open(file_path, "r") as file:
        lines = file.readlines()

    no_gps_periods = []
    current_start = None

    line_nb = 1
    for i, line in enumerate(lines):
        if "GPS|" in line:
            parts = line.split("|")
            timestamp = parts[1]
            gps_data = parts[2]

            if gps_data == "":  # No GPS signal
                if current_start is None:
                    line_nb = i+1
                    current_start = timestamp
            else:  # GPS signal is available
                if current_start is not None:
                    # End of a no GPS period
                    no_gps_periods.append((line_nb, current_start, timestamp))
                    current_start = None

    # If the file ends while still in a no GPS period, record it
    if current_start is not None:
        no_gps_periods.append((line_nb, current_start, lines[-1].split("|")[1]))

    # Calculate and display the duration of each no GPS period
    for i, start, end in no_gps_periods:
        start_time = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        duration = end_time - start_time
        print(f"No GPS from {start} to {end} lasting {duration} starting on line {str(i)}")

    # Display the number of no GPS periods
    print(f"Total number of no GPS periods: {len(no_gps_periods)}")


if __name__ == "__main__":
    pass
