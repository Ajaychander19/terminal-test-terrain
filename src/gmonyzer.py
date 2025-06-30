import csv
import os
import ntpath
from collections import defaultdict
from constantPath import getPathText, getfileName, getOperatorname

class GMonProConverter:
    """This class is used to analyze and convert GMon Pro CSV export files into a structured CSV format.

    It processes one CSV file and produces a new CSV file containing:
      - Cell information (CELLINFO)
      - Serving cell measurements (MEASURE_SERVING)
      - Measurement summaries (MEASUREMENT: RSRP, RSRQ, RSSI)

    The output is structured for compatibility with further processing or visualization.
    """

    COLUMNS = {
        'timestamp': 'TIME',
        'latitude': 'LAT',
        'longitude': 'LON',
        'earfcn': 'ARFCN',
        'pci': 'PCI/PSC/BSIC',
        'rsrp': 'RSRP/RSCP',
        'rsrq': 'RSRQ/ECIO',
        'rssi': 'RSSI',
        'cinr': 'SNR',
        'tac': 'LAC/TAC',
        'cid': 'XCI',
        'plmn': 'PLMN',
    }

    def __init__(self, path, output_directory):
        """Initializes the converter with a CSV input file and an output directory.

        Parameters:
            path (str): path to the input CSV file.
            output_directory (str): directory where the converted file will be saved.
        """        
        self._path = path
        self.output_directory = output_directory
        self.rows = []
        self.count_by_tuple = defaultdict(int)
        self.index_map = {}
        self.mcc = None
        self.mnc = None

    def read_file(self):
        """Reads the CSV file using `csv.DictReader` and returns the list of rows."""
        with open(self._path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            return [row for row in reader]

    def convert(self, data):
        """Converts the list of CSV rows into structured CELLINFO, MEASURE_SERVING and MEASUREMENT entries.

        This function:
          - Extracts necessary parameters from each row
          - Detects cell changes to write CELLINFO rows
          - Creates MEASURE_SERVING and inline MEASUREMENT rows with RSRP/RSRQ/RSSI values
        """
        unique_tuples = sorted(set((row[self.COLUMNS['earfcn']], row[self.COLUMNS['pci']]) for row in data))
        self.index_map = {t: i for i, t in enumerate(unique_tuples)}
        last_tuple = None

        for idx, row in enumerate(data):
            try:
                timestamp = float(idx)
                lat = row[self.COLUMNS['latitude']]
                lon = row[self.COLUMNS['longitude']]
                earfcn = row[self.COLUMNS['earfcn']]
                pci = row[self.COLUMNS['pci']]
                rsrp = row[self.COLUMNS['rsrp']]
                rsrq = row[self.COLUMNS['rsrq']]
                rssi = row[self.COLUMNS['rssi']] or '0'
                cinr = row[self.COLUMNS['cinr']] or '0'
                tac = row[self.COLUMNS['tac']]
                cid = row[self.COLUMNS['cid']]
                plmn = row[self.COLUMNS['plmn']]
                mcc, mnc = plmn[:3], plmn[3:]
                self.mcc, self.mnc = mcc, mnc

                current_tuple = (earfcn, pci)
                self.count_by_tuple[current_tuple] += 1

                # Insert CELLINFO only on change
                if (earfcn, pci, tac, cid) != last_tuple:
                    self.rows.append(["CELLINFO", f"{timestamp:.1f}", lat, lon, earfcn, pci, tac, cid, mcc, mnc])
                    last_tuple = (earfcn, pci, tac, cid)

                # Insert MEASURE_SERVING
                self.rows.append(["MEASURE_SERVING", f"{timestamp:.1f}", lat, lon, earfcn, pci, rsrp, rsrq, rssi, cinr])

                # Immediately insert 3 MEASUREMENT rows for the current sample
                for metric, value in zip(["RSRP", "RSRQ", "RSSI"], [rsrp, rsrq, rssi]):
                    row_measurement = ["MEASUREMENT", f"{timestamp:.1f}", lat, lon, metric]
                    col_values = [''] * len(self.index_map)
                    col_index = self.index_map[current_tuple]
                    col_values[col_index] = value
                    self.rows.append(row_measurement + col_values)

            except Exception as e:
                print(f"Skipping line {idx} due to error: {e}")

    def write_output(self):
        """Writes the final structured CSV file with headers and formatted rows.

        It includes metadata headers (VERSION, TECHNO...), EARFCN/PCI/BEAM lists, and all measurement entries.
        """
        operator = getOperatorname(self.mcc, self.mnc)
        filename = getfileName(self._path)
        output_file = os.path.join(self.output_directory, f"cev{operator}_{filename}.csv")

        tuples = sorted(self.index_map.keys())
        earfcns = [t[0] for t in tuples]
        pcis = [t[1] for t in tuples]
        beams = ['0'] * len(tuples)
        nb_meas = [str(self.count_by_tuple[t]) for t in tuples]
        n = len(tuples)

        with open(output_file, 'w', newline='', encoding='utf-8') as out:
            writer = csv.writer(out, delimiter='|')

            # Header
            writer.writerow(['DEFINE'])
            writer.writerow(['VERSION', 'Version'])
            writer.writerow(['DATE', 'Date'])
            writer.writerow(['TECHNO', 'Techno'])
            writer.writerow(['MEAS_EARFCNS', 'NA', 'NA', 'NA', 'NA'] + [f'EARFCN_{i}' for i in range(n)])
            writer.writerow(['MEAS_PCIS', 'NA', 'NA', 'NA', 'NA'] + [f'PCI_{i}' for i in range(n)])
            writer.writerow(['MEAS_BEAMS', 'NA', 'NA', 'NA', 'NA'] + [f'BEAM_{i}' for i in range(n)])
            writer.writerow(['MEAS_NB', 'NA', 'NA', 'NA', 'NA'] + [f'nb_meas_{i}' for i in range(n)])

            writer.writerow(['CELLINFO', 'Timestamp', 'Lat', 'Lng', 'EARFCN', 'PCI', 'TAC', 'CID', 'MCC', 'MNC'])
            writer.writerow(['MEASURE_SERVING', 'Timestamp', 'Lat', 'Lng', 'Serving_EARFCN', 'Serving_PCI', 'Serving_RSRP', 'Serving_RSRQ', 'Serving_RSSI', 'Serving_CINR'])
            writer.writerow(['MEASUREMENT','Timestamp','Lat','Lng','Measurement_Name'] + [''] * len(self.index_map))

            writer.writerow(['CONTENT'])
            writer.writerow(['VERSION', '2.0'])
            writer.writerow(['DATE', 'NULL'])
            writer.writerow(['TECHNO', '4G'])

            writer.writerow(['MEAS_EARFCNS', '', '', '', ''] + earfcns)
            writer.writerow(['MEAS_PCIS', '', '', '', ''] + pcis)
            writer.writerow(['MEAS_BEAMS', '', '', '', ''] + beams)
            writer.writerow(['MEAS_NB', '', '', '', ''] + nb_meas)

            # Write all content rows (CELLINFO, MEASURE_SERVING + MEASUREMENT)
            for row in self.rows:
                writer.writerow(row)

        print(f"File converted: {output_file}")

    def process(self):
        data = self.read_file()
        self.convert(data)
        self.write_output()
