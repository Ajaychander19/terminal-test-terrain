import os

import logging
import sys
import time
from datetime import datetime

from SerialConnection import SerialConnection


def setup_logger(name: str, log_file_path: str):
    """
    Set up a logger with a given name and at given log file path.

    :param name: Name of the logger
    :param log_file_path: Path to the log file (logger will create it if it doesn't exist)
    :return:
    """
    formatter = logging.Formatter('%(asctime)s - %(message)s')

    handler = logging.FileHandler(log_file_path)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger


logs_dir = f'./logs/{datetime.now().strftime("%Y-%m-%d")}'
if not os.path.isdir(logs_dir):
    os.makedirs(logs_dir)

# Configure logger for processed output
nmea_logger = setup_logger('nmea_logger', f'{logs_dir}/nmea_logger.log')
# Configure logger for raw output
raw_logger = setup_logger('raw_nmea_logger', f'{logs_dir}/raw_nmea.log')
raw_logger.addHandler(logging.StreamHandler(sys.stdout))


def parse_gsv(line: str) -> tuple[int, str, list[tuple[str, str, str, str, str]]]:
    """
    Parse a $--GSV line from the NMEA output and return the satellites seen.
    The line must be of the correct format which should be checked before calling this function.

    :param line: A line with text from the NMEA output
    :return: nb_satellites (int): The amount of satellites seen according to the line,
             satellite_type (str): The type (like GPS or GLONASS) of the satellites in this line,
             satellites (List[Tuple(sat_id: int, sat_type: str, elevation: str, azimuth: str, snr: str)]:
                The different satellites seen in this line. All values of the satellite are numbers in string form
    """
    parts: list[str] = line.strip().split(',')
    # There are two ways of knowing the satellite type, but I'm not sure if either of them is reliable
    if parts[0].startswith("$GP"):
        satellites_type = "GPS"
    elif parts[0].startswith("$GL"):
        satellites_type = "GLONASS"
    elif parts[0].startswith("$GA"):
        satellites_type = "GALLILEO"
    elif parts[0].startswith("$BD"):
        satellites_type = "BEIDOU"
    else:
        satellites_type = "Unknown"

    nb_satellites = int(parts[3])
    satellites = []

    # Starting from the 4th value, we get 4 values for each satellite (and there can be multiple satellites)
    for i in range(4, len(parts) - 1, 4):
        if parts[i]:
            sat_id = int(parts[i])
            elevation = parts[i + 1] if parts[i + 1] else 'N/A'
            azimuth = parts[i + 2] if parts[i + 2] else 'N/A'
            snr = parts[i + 3] if parts[i + 3] else 'N/A'

            # Determine satellite type (according to the documentation found online)
            if 1 <= sat_id <= 37 and parts[0].startswith("$BD"):
                sat_type = "Beidou"
            elif 1 <= sat_id <= 32:
                sat_type = "GPS"
            elif 33 <= sat_id <= 64:
                sat_type = "SBAS"
            elif 65 <= sat_id <= 96:
                sat_type = "GLONASS"
            elif 193 <= sat_id <= 197:
                sat_type = "QZSS"
            else:
                sat_type = "Unknown"

            satellites.append((str(sat_id), sat_type, elevation, azimuth, snr))

    return nb_satellites, satellites_type, satellites


def log_gnss_data(port='/dev/ttyUSB1'):
    # Wait until the NMEA output port is open
    while not os.path.exists(port):
        time.sleep(0.5)

    with SerialConnection(port_path=port, baudrate=9600, timeout=1, logger=nmea_logger, encoding="ascii") as ser:
        nmea_logger.info("")  # Empty line to separate the logs of the same day
        nmea_logger.info("Module booted, starting collecting satellite information")
        nmea_logger.info("Total satellites: N, Satellite info: List[Tuple(sat_id, sat_type, "
                         "elevation, azimuth, snr)]")
        while True:
            try:
                line = ser.readline().strip()
                raw_logger.info(line)  # Log the raw NMEA message
                if line.startswith('$') and 'GSV' in line:
                    result = parse_gsv(line)
                    if result is not None:
                        nb_satellites, satellites_type, satellites = result
                        log_message = (f"Total satellites: {nb_satellites}, Type: {satellites_type}, "
                                       f"Satellite info: {satellites}")
                        nmea_logger.info(log_message)
            except Exception as e:
                nmea_logger.error(f"Error reading from serial port: {e}")
            time.sleep(0.3)


if __name__ == "__main__":
    log_gnss_data()
