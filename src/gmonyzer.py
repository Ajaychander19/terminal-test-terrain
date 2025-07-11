import csv
import os
from collections import defaultdict
from constantPath import getfileName, getOperatorname
from typing import List
from datetime import datetime

class GMonProMerger:
    """
    This class merges several G-MoN Pro CSV files into a single CSV.
    The header from the first file is kept.
    """

    def __init__(self):
        print("Merging G-MoNPro files...")

    def merge(self, output_dir: str, file_list: List[str]) -> str:
        content_lines = []
        timestamps = []
        base_header = []

        for path in sorted(file_list):
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                lines = list(reader)

                # Save the header from the first file
                if not base_header:
                    base_header = reader.fieldnames

                for row in lines:
                    if row: 
                        # Convert all values to string and handle missing columns
                        content_lines.append([row.get(col, '') for col in base_header])

                # Extract the first date from the file
                for row in lines:
                    date_str = row.get("DATE", "").strip()
                    if date_str and date_str.upper() != "NULL":
                        try:
                            timestamps.append(datetime.strptime(date_str, "%Y/%m/%d"))
                        except ValueError:
                            pass
                        break

        # Generate the output filename based on the date range
        timestamps = sorted(timestamps)
        if timestamps:
            start_str = timestamps[0].strftime("%Y%m%d")
            end_str = timestamps[-1].strftime("%Y%m%d")
        else:
            start_str = end_str = datetime.now().strftime("%Y%m%d")

        base_name = f"merged_gmonpro_{start_str}_to_{end_str}"
        merged_filename = f"{base_name}.csv"
        merged_path = os.path.join(output_dir, merged_filename)

        # Add a counter to avoid overwriting existing files
        counter = 1
        while os.path.exists(merged_path):
            merged_filename = f"{base_name}_{counter}.csv"
            merged_path = os.path.join(output_dir, merged_filename)
            counter += 1

        # Write the merged content to the new CSV file
        with open(merged_path, "w", newline='', encoding='utf-8') as out:
            writer = csv.writer(out, delimiter=';')
            writer.writerow(base_header)
            writer.writerows(content_lines)

        print(f"Merged file created: {merged_path}")
        return merged_path




class GMonProConverter:
    """This class is used to analyze and convert GMon Pro CSV export files into a structured CSV format.

    It processes one CSV file and produces a new CSV file containing:
      - Cell information (CELLINFO)
      - Serving cell measurements (MEASURE_SERVING)
      - Measurement summaries (MEASUREMENT: RSRP, RSRQ, RSSI)

    The output is structured for compatibility with further processing or visualization.
    """

    # Mapping of CSV columns to expected names in the output
    COLUMNS = {
        'timestamp': 'TIME',
        'latitude': 'LAT',
        'longitude': 'LON',
        'earfcn': 'ARFCN',
        'pci': 'PCI/PSC/BSIC',
        'rsrp': 'RSRP/RSCP',
        'rsrq': 'RSRQ/ECIO',
        'rssi': 'RSSI',
        # 'cinr': 'SNR',
        'tac': 'LAC/TAC',
        'cid': 'XCI',
        'plmn': 'PLMN',
        'ta': 'TA',
        'date': 'DATE'
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
        self.row_date= [] 
        self.count_by_tuple = defaultdict(int) # Dictionary to count occurrences of (EARFCN, PCI) tuples
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
        # Create a mapping of (EARFCN, PCI) tuples to their index, ignoring empty values
        unique_tuples = sorted(set(
            (row[self.COLUMNS['earfcn']].strip(), row[self.COLUMNS['pci']].strip())
            for row in data
            if row[self.COLUMNS['earfcn']].strip() != '' and row[self.COLUMNS['pci']].strip() != ''
        ))
        self.index_map = {t: i for i, t in enumerate(unique_tuples)} # Create a mapping from (EARFCN, PCI) tuples to their index, it will be used to fill the MEASUREMENT rows
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
                rssi = row[self.COLUMNS['rssi']] or '-1'
                cinr = -1
                tac = row[self.COLUMNS['tac']]
                cid = row[self.COLUMNS['cid']]
                plmn = row[self.COLUMNS['plmn']]
                mcc, mnc = plmn[:3], plmn[3:]
                ta = row[self.COLUMNS['ta']]
                self.mcc, self.mnc = mcc, mnc
                date = row[self.COLUMNS['date']]

                # Clean and validate inputs
                cid = row.get(self.COLUMNS['cid'], '').strip()
                plmn = row.get(self.COLUMNS['plmn'], '').strip()
                rsrp = row.get(self.COLUMNS['rsrp'], '').strip()
                rsrq = row.get(self.COLUMNS['rsrq'], '').strip()

                # Check for missing values
                if plmn == '000000' or cid == '' or rsrp == '' or rsrq == '':
                    print(f"[IGNORE] Line {idx} ignored : missing values (CID/PLMN/RSRP/RSRQ)")
                    continue


                current_tuple = (earfcn, pci)
                if current_tuple not in self.index_map:
                    print(f"[IGNORE] Tuple {current_tuple} missing to index_map at the line {idx}")
                    continue
                self.count_by_tuple[current_tuple] += 1

                # Insert CELLINFO only on change
                if (earfcn, pci, tac, cid) != last_tuple:
                    self.rows.append(["CELLINFO", f"{timestamp:.1f}", lat, lon, earfcn, pci, tac, cid, mcc, mnc])
                    last_tuple = (earfcn, pci, tac, cid)

                # Insert MEASURE_SERVING
                self.rows.append(["MEASURE_SERVING", f"{timestamp:.1f}", lat, lon, earfcn, pci, rsrp, rsrq, rssi, cinr, ta])

                # Immediately insert 3 MEASUREMENT rows for the current sample
                for metric, value in zip(["RSRP", "RSRQ", "RSSI"], [rsrp, rsrq, rssi]):
                    row_measurement = ["MEASUREMENT", f"{timestamp:.1f}", lat, lon, metric]
                    col_values = [''] * len(self.index_map)
                    col_index = self.index_map[current_tuple]
                    col_values[col_index] = value
                    self.rows.append(row_measurement + col_values)
                
                self.row_date.append(date)  # Store the date for later use

            except Exception as e:
                print(f"Skipping line {idx} due to error: {e}")

    def write_output(self):
        """Writes the final structured CSV file with headers and formatted rows.

        It includes metadata headers (VERSION, TECHNO...), EARFCN/PCI/BEAM lists, and all measurement entries.
        """
        operator = getOperatorname(self.mcc, self.mnc)
        filename = getfileName(self._path)
        output_file = os.path.join(self.output_directory, f"cev{operator}_{filename}.csv") # Construct output filename with operator and original filename

        tuples = sorted(self.index_map.keys())  # Sort tuples for consistent order
        earfcns = [t[0] for t in tuples]
        pcis = [t[1] for t in tuples]
        beams = ['0'] * len(tuples)
        nb_meas = [str(self.count_by_tuple[t]) for t in tuples] # Count of measurements for each (EARFCN, PCI) tuple
        n = len(tuples) # Number of unique (EARFCN, PCI) tuples
        
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
            writer.writerow(['MEASURE_SERVING', 'Timestamp', 'Lat', 'Lng', 'Serving_EARFCN', 'Serving_PCI', 'Serving_RSRP', 'Serving_RSRQ', 'Serving_RSSI', 'Serving_CINR', 'Serving_TA'])
            writer.writerow(['MEASUREMENT','Timestamp','Lat','Lng','Measurement_Name', 'Values'])

            writer.writerow(['CONTENT'])
            writer.writerow(['VERSION', '2.0'])
            writer.writerow(['DATE', self.row_date[0]])
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
