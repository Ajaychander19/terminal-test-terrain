"""This module defines CellAssociator class and methods to associate base stations / antennas to each measurement."""

from collections import defaultdict
import math
import os.path
import pathlib
import pandas as pd
import numpy as np
import csvtools as csvt
import shapely.geometry as geom
import scipy.spatial as sp
from dictutils import insert_data
from scipy.spatial.distance import pdist
import csv
from datetime import datetime
import copy
from pathlib import Path
import os


# fichier où l'on log
CSV_LOG_FILE = "scores_log.csv"
debug = False

# if debug = true créer csv qui donne valeur de ta, distance pour chaque point le meilleur site et les 2 suivants, retirer delta/2 si tjrs sup

TOP3_CSV_FILE = "top3_sites_par_point.csv"

def init_csv_top3(csv_path=TOP3_CSV_FILE):
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=';')
        header = ["pci", "earfcn", "lat", "lng"]
        for k in (1, 2, 3):
            header += [
                f"best_site_{k}", f"dist_{k}", f"L_{k}", f"ta_{k}",
                f"score_ajt_{k}", f"score_cumule_{k}"
            ]
        w.writerow(header)

def log_top3_row(pci, earfcn, lat, lng, top3_data, csv_path=TOP3_CSV_FILE):
    """
    top3_data = list of 3 elements (or fewer):
    [(site, dist, L, ta, score_ajt, score_cumule), ...]
    Missing spaces are filled with zeros.
    """
    with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=';')
        row = [pci, earfcn, f"{lat:.6f}", f"{lng:.6f}"]
        for k in range(3):
            if k < len(top3_data):
                site, dist, L, ta, s_ajt, s_cum = top3_data[k]
                row += [
                    site,
                    f"{dist:.1f}", f"{L:.1f}", ta,
                    f"{s_ajt:.6f}", f"{s_cum:.6f}"
                ]
            else:
                row += ["", "0.0", "0.0", "", "0.000000", "0.000000"]
        w.writerow(row)

class CellAssociator:

    """This class allows to do the association between measurements and mobile network base stations.


    Measurement data are stored in the CSV file produced by the filed-testing functionality, and base stations

    data are stored in the "sites" file produced during Cartoradio Processing.


    Using these two files, the association between measurements and mobile network base stations is done. There is

    no trivial relation between measurements and base stations: several criteria are used to find the relation. Grouping

    measurement points by EARFCN / PCI, these criteria are:


    - Signal reception criteria: how good is the received signal ?

    - Angular criteria: is the point clearly in the angle forming the sector of the antenna ?

    - Cell belonging criteria : is the point clearly in the cell.


    Based on these criteria, this is possible to associate each group of measurements with the EARFCN / PCI to an

    antenna, and so to a base station.

    """

    # Association file header

    _HEADER = {

        'MEAS_EARFCNS': ['NA', 'NA', 'NA', 'NA', 'EARFCN1', 'EARFCN2', 'EARFCN3', 'etc'],

        'MEAS_PCIS': ['NA', 'NA', 'NA', 'NA', 'PCI1', 'PCI2', 'PCI3', 'etc'],

        'MEAS_NB': ['NA', 'NA', 'NA', 'NA', 'nb_meas_for_1', 'nb_meas_for_2', 'nb_meas_for_3', 'etc'],

        'MEASUREMENT': ['Timestamp', 'Lat', 'Lng', 'Measurement_Name'],

        'DELIMITER': ['Cartoradio_Number', 'Support_Lat', 'Support_Lng', 'Del_Lat', 'Del_Lng'],

        'BS_ANT_DIR': ['Cartoradio_Number', 'Ant_Number', 'Support_Lat', 'Support_Lng', 'Dest_Lng', 'Dest_Lat', 'Height'],

        'ASSOC': ['Cartoradio_Number', 'Ant_Number', 'TAC', 'CID', 'EARFCN', 'PCI'],

        'POINT': ['Lat', 'Lng', 'TAC', 'CID', 'EARFCN', 'PCI', 'RSRP', 'RSRQ', 'RSSI', 'CINR']

    }

    # Association file header V2

    _HEADER_V2 = {

        'VERSION': ['Version'],

        'TECHNO': ['Techno'],

        'START_DATE': ['Date'],

        'END_DATE': ['Date'],

        'MEAS_EARFCNS': ['NA', 'NA', 'NA', 'NA'],

        'MEAS_PCIS': ['NA', 'NA', 'NA', 'NA'],

        'MEAS_BEAMS': ['NA', 'NA', 'NA', 'NA'],

        'MEAS_NB': ['NA', 'NA', 'NA', 'NA'],

        'MEASUREMENT': ['Timestamp', 'Lat', 'Lng', 'Measurement_Name'],

        'DELIMITER': ['Cartoradio_Number', 'Support_Lat', 'Support_Lng', 'Del_Lat', 'Del_Lng'],

        'BS_ANT_DIR': ['Cartoradio_Number', 'Ant_Number', 'Support_Lat', 'Support_Lng', 'Dest_Lng', 'Dest_Lat', 'Height'],

        'ASSOC': ['Cartoradio_Number', 'Ant_Number', 'TAC', 'CID', 'EARFCN', 'PCI', 'Score'],

        'MEASURE_SERVING': ['Lat', 'Lng', 'TAC', 'CID', 'EARFCN', 'PCI', 'BEAM', 'RSRP', 'RSRQ', 'RSSI', 'CINR']

    }

    def __init__(self, in_meas: str, in_sites: str, outdir: str):

        """Class constructor.

        Parameters:
            in_meas: path of the input measurement file.
            in_sites: path of the input "sites" file.
            outdir: path of the output file.
        """
        self._in_sites = in_sites   # Sites file path.
        self._in_meas = in_meas     # Measurements file path ad name.
        self._outdir = outdir       # Output file directory.
        self._measure_point = None    # Association between points and measurements.
        self._antennas = None       # Antennas
        self.version = None
        self.techno = "4G"
        self.start_date = None
        self.end_date = None


    def process_asso(self) -> str:
        """ 1 = RSRP filtered by TA (a single *_FUSION.csv file, no intermediate files)
            2 = TA association only (writes *_TA.csv)
            3 = RSRP association only (writes *.csv)"""
        
        mode = 3 # 1=RSRP and TA, 2=TA only, 3=RSRP only
        if mode == 1:
            return self.associate_single_pass_with_ta_filter(mode=1)

        elif mode == 2:
            self.calculate_association_TA()
            out = os.path.join(
                self._outdir,
                f"assoc_{Path(self._in_meas).stem.replace('cev','')}_{Path(self._in_sites).stem.replace('cev','')}_TA.csv"
            )
            return out

        elif mode == 3:
            return self.calculate_association(1, '', keep_only_keys=None, out_name='assoc_{0}_{1}.csv')

        else:
            raise ValueError("Invalid mode. 1=RSRP and TA, 2=TA only, 3=RSRP only")


    def _prepare_header_for_writer(self, header: dict) -> None:
        """Read DEFINE bloc of measurement file and extend line accordingly"""

        # Open measurement file for reading
        with open(self._in_meas, 'r', encoding='utf-8', errors='ignore') as fin:

            # Scans the file line by line
            for raw in fin:

                # Removes the trailing line break
                line = raw.rstrip('\n')

                # Ignores empty lines
                if not line:
                    continue

                # Cuts on '|': tag = first field, rest = rest of the line
                tag, *rest = line.split('|')

                # Ending of DEFINE bloc
                if tag == 'CONTENT':
                    break

                # Get the version if present and convert it to float
                if tag == 'VERSION':
                    try: self.version = float(rest[0])
                    except: pass

                elif tag == 'TECHNO':
                    self.techno = rest[0]

                # Number of dynamic columns after 4 NA
                elif tag == 'MEAS_EARFCNS':
                    n = max(0, len(rest) - 4)  # nb of EARFCN_* to add
                    header['MEAS_EARFCNS'] += [f'EARFCN_{i}' for i in range(n)]
                elif tag == 'MEAS_PCIS':
                    n = max(0, len(rest) - 4)
                    header['MEAS_PCIS'] += [f'PCI_{i}' for i in range(n)]
                elif tag == 'MEAS_BEAMS':
                    n = max(0, len(rest) - 4)
                    header['MEAS_BEAMS'] += [f'BEAM_{i}' for i in range(n)]
                elif tag == 'MEAS_NB':
                    n = max(0, len(rest) - 4)
                    header['MEAS_NB'] += [f'nb_meas_{i}' for i in range(n)]
                elif tag == 'MEASUREMENT':
                    n = max(0, len(rest) - 4)
                    header['MEASUREMENT'] += [f'Meas_{i}' for i in range(n)]


    def calculate_association_TA(self):
        """Calculates the association between EARFCNs / PCIs and base stations using timing advance."""

        print('Starting association...')

        file_meas = pathlib.Path(self._in_meas)
        file_sites = pathlib.Path(self._in_sites)

        file_name = os.path.join(self._outdir, 'assoc_{0}_{1}_TA.csv'.format(
                    pathlib.Path(self._in_meas).stem.replace("cev",""),
                    pathlib.Path(self._in_sites).stem.replace("cev","")))
        
        header = self._HEADER_V2
        

        with csvt.CSVReader(self._in_meas) as meas:
            for _ in range(10):
                line = meas.read_line()
                if not line:
                    break

                if line[0] == 'VERSION':

                    self.version = float(line[1])
                    header = self._HEADER_V2
                    header['START_DATE'] = ['Date']
                    header['END_DATE'] = ['Date']
                
                if line[0] == 'START_DATE':
                    self.start_date = line[1]

                if line[0] == 'END_DATE':
                    self.send_date = line[1]

                if line[0] == 'TECHNO':
                    self.techno = str(line[1])

                if line[0] == 'MEAS_EARFCNS':

                    n = len(line) - 5

                    header['MEAS_EARFCNS'] = header['MEAS_EARFCNS'] + ['EARFCN_{}'.format(i) for i in range(n)]
                    header['MEAS_PCIS'] = header['MEAS_PCIS'] + ['PCI_{}'.format(i) for i in range(n)]
                    header['MEAS_BEAMS'] = header['MEAS_BEAMS'] + ['BEAM_{}'.format(i) for i in range(n)]
                    header['MEAS_NB'] = header['MEAS_NB'] + ['nb_meas_{}'.format(i) for i in range(n)]
                    header['MEASUREMENT'] = header['MEASUREMENT'] + ['Meas_{}'.format(i) for i in range(n)]
                    break
            
            
        with csvt.CSVWriter(file_name, header) as out_wr:

            print('Reading measurements...')

            self._read_measurements(out_wr) # Measurements

            print('Reading sites...')

            self._read_antennas(out_wr) # Delimiter

            print('Identifying possible Associations...')
            print('Input files: {0} and {1}'.format(file_meas, file_sites))
            self._associate_data_with_TA()
            
            self._write_output(out_wr)

    def calculate_association(self, mode: int, assoc_file: str, keep_only_keys: set[tuple] | None = None, out_name: str | None = None):
        """Calculates the association between EARFCNs / PCIs and base stations."""

        print('Starting association...')

        # Construct file name
        file_name = os.path.join(
            self._outdir, # target folde
            (out_name if out_name else 'assoc_{0}_{1}.csv').format(
                pathlib.Path(self._in_meas).stem.replace("cev",""),
                pathlib.Path(self._in_sites).stem.replace("cev",""))
        )

        # independent copy
        header = copy.deepcopy(self._HEADER_V2)

        # Extends measure lines of header
        self._prepare_header_for_writer(header)

        # Open writer
        with csvt.CSVWriter(file_name, header) as out_wr:
            print('Reading measurements...'); self._read_measurements(out_wr) # Reads measurement file, fills self._measure_point and copies the useful DEFINE lines
            print('Reading sites...');        self._read_antennas(out_wr) # Reads the sites, fills self._antennas and copies the DELIMITER
            if mode == 1:
                print('Identifying possible Associations...')

                # Filter of association with TA
                allowed_ep = None
                if keep_only_keys:
                    allowed_ep = {(e, p) for (_,_,_,_,e,p) in keep_only_keys}
                self._associate_data(allowed_ep=allowed_ep) # Compute assoc with RSRP using only these pairs
            else:
                print('Using association file...'); self._associate_read(assoc_file) 
            print('Writing output...')
            self._write_output(out_wr, keep_only_keys=keep_only_keys) # write BS_ANT_DIR, ASSOC and MEASURE_SERVING
        
        # reset dynamic header
        header['MEAS_EARFCNS'] = ['NA','NA','NA','NA']
        header['MEAS_PCIS'] = ['NA','NA','NA','NA']
        header['MEAS_BEAMS'] = ['NA','NA','NA','NA']
        header['MEAS_NB'] = ['NA','NA','NA','NA']
        header['MEASUREMENT'] = ['Timestamp','Lat','Lng','Measurement_Name']
        return file_name

    def associate_single_pass_with_ta_filter(self, mode: int = 1, assoc_file: str = '') -> str:
        """ Computes in memory the associations from the Timing Advance (TA) -> set of keys.
            Runs the standard association and only writes the ASSOCs whose key is present on the TA side.
            If no TA key is found, writes the complete standard association.

            Args:
            mode: 1 = compute associations; 0 = reread an existing association file.
            assoc_file: path to the CSV file of associations to reread if mode==0.

            Returns:
            Path to the produced CSV file:
            - *_FUSION.csv if a TA filter is applied,
            - *.csv otherwise."""
        ta_keys = self.compute_ta_assoc_keys()  # calculates all TA associations in memory (no file created)

        # If no TA detected only execute the association method with the RSRP
        if not ta_keys:
            return self.calculate_association(mode, assoc_file, keep_only_keys=None, out_name='assoc_{0}_{1}.csv')
        return self.calculate_association(
            mode, assoc_file, keep_only_keys=ta_keys, out_name='assoc_{0}_{1}_FUSION.csv'
        )


    def compute_ta_assoc_keys(self) -> set[tuple]:
        """ Calculates the associations using Timing Advance and returns
            all the association keys.

            Key = (Cartoradio_Number, Ant_Number, TAC, CID, EARFCN, PCI) as integers."""
        
        # Resets variables before reading
        self._measure_point = None
        self._antennas = None

        # Loads input data without writing anything
        self._read_measurements(_NullWriter())
        self._read_antennas(_NullWriter())

        # Associates with TA and fills self._assoc
        self._associate_data_with_TA()

        # Contains normalize keys
        ta_keys = set()

        # Alias for readability
        A = self._assocs

        # Iterates over all produced associations
        for i in range(len(A['Cartoradio_Number'])):
            key = (
                to_int_token(A['Cartoradio_Number'][i]),
                to_int_token(A['Ant_Number'][i]),
                to_int_token(A['TAC'][i]),
                to_int_token(A['CID'][i]),
                to_int_token(A['EARFCN'][i]),
                to_int_token(A['PCI'][i]),
            )
            ta_keys.add(key) # Add key to set
        return ta_keys

    def _read_measurements(self, out_wr: csvt.CSVWriter):

        """PRIVATE METHOD which reads measurement file.

        Reads the measurement file and store data in memory.
        MEAS_EARFCNS, MEAS_PCIS and MEASUREMENT fields are reproduced in the output file.

        Parameters:
            out_wr: output file to be written.

        Raises:
            RuntimeError: if a problem occurs while decoding data from the file.
        """

        # Serving cell infos.
        serving_dict = {
            'Timestamp': [], 'Lat': [], 'Lng': [], 'EARFCN': [], 'PCI': [], 'BEAM': [],
            'RSRP': [], 'RSRQ': [], 'RSSI': [], 'CINR': [], 'TA': []
        }

        # Found cells information (SIB1).
        cellinfo_dict = {'EARFCN': [], 'PCI': [], 'TAC': [], 'CID': []}

        # EARFCNs / PCIs
        earpcis = []

        # Reading measurement file...

        with csvt.CSVReader(self._in_meas) as meas:

            line = meas.read_line()     # Current line.
            last_valid_line = None
            boolean_version = False
            while line != ['']:

                # Registering base stations.
                try:
                    if line[0] == 'CELLINFO':

                        if len(line) < 10:
                            raise RuntimeError('error: CELLINFO line must contain at least 10 fields')

                        insert_data(
                            cellinfo_dict,
                            {'EARFCN': [int(line[4])], 'PCI': [int(line[5])], 'TAC': [int(line[6])], 'CID': [int(line[7])]},
                            1
                        )

                    elif line[0] == 'VERSION':
                        boolean_version = True
                        if float(line[1]) < 3.0:
                            raise RuntimeError('error: this measurement file is not compatible with this version of the program, please use a newer version.')
                        
                        self.version = 3.0
                        out_wr.write_row(line)
                    if not boolean_version:
                        raise RuntimeError('error: this measurement file does not contain a VERSION line, please use a newer version of the program.')
                    
                    elif line[0] == 'START_DATE':
                        out_wr.write_row(line)

                    elif line[0] == 'END_DATE':
                        out_wr.write_row(line)

                    elif line[0] == 'TECHNO':
                        out_wr.write_row(line)
                        self.techno = str(line[1])

                    # Registering measurements...
                    elif line[0] == 'MEASURE_SERVING':
                        #print(f"techno is {self.techno}\n")

                        if self.techno == "5G NR":
                            
                            try:
                                # Verifying that all required fields are present in the line.
                                required_fields = line[1:10] 
                                if any(val.strip() == '' for val in required_fields):
                                    raise ValueError(f"Missing values into MEASURE_SERVING at the line: {line}")
                                
                                ta_value = float(line[10]) if len(line) > 10 and line[10].strip() != '' else None

                                insert_data(

                                    serving_dict,

                                    {'Timestamp': [float(line[1])], 'Lat': [float(line[2])],
                                    'Lng': [float(line[3])], 'EARFCN': [int(line[4])], 'PCI': [int(line[5])],
                                    'BEAM': [int(line[6])],
                                    'RSRP': [float(line[7])], 'RSRQ': [float(line[8])], 'RSSI': [float(line[9])],
                                    'CINR': [float(line[10])], 'TA': [ta_value]}, 

                                    1

                                )
                            except ValueError as e:
                                print(f"[ERROR] MEASURE_SERVING incorrectin 5G")


                        else:
                            try:
                                # Verifying that all required fields are present in the line.
                                required_fields = line[1:10] 
                                if any(val.strip() == '' for val in required_fields):
                                    raise ValueError(f"Missing values into MEASURE_SERVING at the line: {line}")
                                
                                ta_value = float(line[10]) if len(line) > 10 and line[10].strip() != '' else None

                                insert_data(

                                    serving_dict,

                                    {'Timestamp': [float(line[1])], 'Lat': [float(line[2])],
                                    'Lng': [float(line[3])], 'EARFCN': [int(line[4])], 'PCI': [int(line[5])],
                                    'BEAM': [0],
                                    'RSRP': [float(line[6])], 'RSRQ': [float(line[7])], 'RSSI': [float(line[8])],
                                    'CINR': [float(line[9])], 'TA': [ta_value]}, 

                                    1

                                )
                            except ValueError as e:
                                print(f"[ERROR] MEASURE_SERVING incorrect line : {e}")

                    # Registering EARFCN / PCI / BEAM (if V2) tuples...
                    elif line[0] == 'MEAS_EARFCNS':

                        if len(line) < 6:
                            raise RuntimeError('error: MEAS_EARFCNS line must contain at least 6 fields')

                        lineb = meas.read_line()

                        if lineb[0] != 'MEAS_PCIS':
                            raise RuntimeError('error: MEAS_EARFCNS line must be followed by MEAS_PCIS line.')

                        if len(lineb) < 6:
                            raise RuntimeError('error: MEAS_PCIS line must contain at least 6 fields')

                        if len(line) != len(lineb):
                            raise RuntimeError('error: MEAS_EARFCNS and MEAS_PCIS line should have the same length.')

                        earpcis = None

                        if self.version == 3.0:
                            linec = meas.read_line()
                            earpcis = [(int(i), int(j), int(k)) for (i, j, k) in zip(line[5:], lineb[5:], linec[5:])]
                            out_wr.write_row(line)
                            out_wr.write_row(lineb)
                            out_wr.write_row(linec)

                        else:
                            # Writing couples in file...
                            out_wr.write_row(line)
                            out_wr.write_row(lineb)
                            earpcis = [(int(i), int(j)) for (i, j) in zip(line[5:], lineb[5:])]

                    elif line[0] == 'MEAS_NB':
                        if len(line) != len(lineb):
                            raise RuntimeError('error: MEAS_PCIS and MEAS_NB lines should have the same length.')
                        out_wr.write_row(line)     # writing the number of meas samples (which is just after the list of PCIS and with the same length)

                    # Registering measurement data...
                    elif line[0] == 'MEASUREMENT':
                        if not earpcis:
                            raise RuntimeError('error: EARFCNS/PCIS not declared.')
                        out_wr.write_row(line)

                    elif line[0] == 'MEAS_PCIS':
                        raise RuntimeError('error: MEAS_PCIS line must be directly preceded by a MEAS_EARFCNS line.')

                except Exception as e:
                    print(f"[Error] : {e}")
                    raise RuntimeError(f"Last correct line before error : {last_valid_line}")
                
                last_valid_line = line
                line = meas.read_line()

            # Associating measurement points to corresponding base stations...
            self._measure_point = pd.merge(
                pd.DataFrame(cellinfo_dict), pd.DataFrame(serving_dict),
                on=['EARFCN', 'PCI']
            ).drop_duplicates(subset=['Timestamp']).sort_values(['Timestamp'])

        df_meas = self._measure_point.copy()

        # Compute mean and std for Lat and Lng
        lat_mean = df_meas['Lat'].mean()
        lng_mean = df_meas['Lng'].mean()
        lat_std = df_meas['Lat'].std()
        lng_std = df_meas['Lng'].std()

        # Define the filtering range (mean +/- 4 standard deviations)
        lat_min, lat_max = lat_mean - 4 * lat_std, lat_mean + 4 * lat_std
        lng_min, lng_max = lng_mean - 4 * lng_std, lng_mean + 4 * lng_std

        # Delete points outside the defined range
        filtered = []
        for i, row in df_meas.iterrows():
            if not (lat_min <= row['Lat'] <= lat_max) or not (lng_min <= row['Lng'] <= lng_max):
                print(f"[FILTER] Excluded GPS point at lat={row['Lat']}, lng={row['Lng']}")
            else:
                filtered.append(row)

        # Update the measure_point DataFrame with filtered data
        self._measure_point = pd.DataFrame(filtered)

    def _read_antennas(self, out_wr: csvt.CSVWriter):

        """PRIVATE METHOD which reads "sites" file.
        Reads the "sites" file and store its data in memory.
        DELIMITER fields are reproduced in the output file.

        Parameters:
            out_wr: output file to be written.

        Raises:
            RuntimeError: if a problem occurs while decoding data from the file.
        """

        # Antennas data
        antennas_dict = {
            'Cartoradio_Number': [], 'Ant_Number': [], 'Lat': [], 'Lng': [], 'Dest_Lat': [], 'Dest_Lng': [],
            'Azimuth': [], 'AzimuthMin': [], 'AzimuthMax': [], 'Height': []
        }

        version_boolean = False

        # Reading antenna file...
        with csvt.CSVReader(self._in_sites) as sites:

            line = sites.read_line()

            while line != ['']:

                if line[0] == 'VERSION':
                    version_boolean = True
                    if float(line[1]) < 3.0:
                        raise RuntimeError('error: this site file is not compatible with this version of the program, please use a newer version.')
                    
                if version_boolean == False:
                    raise RuntimeError('error: this site file does not contain a VERSION line, please use a newer version of the program.')

                # Antenna info...
                if line[0] == 'BS_ANTENNA':

                    insert_data(
                        antennas_dict,
                        {
                            'Cartoradio_Number': [int(line[2])], 'Ant_Number': [int(line[8])],
                            'Lat': [float(line[3])], 'Lng': [float(line[4])], 'Dest_Lat': [float(line[9])],
                            'Dest_Lng': [float(line[10])], 'Azimuth': [float(line[11])],
                            'AzimuthMin': [float(line[12])],  'AzimuthMax': [float(line[13])], 'Height': [float(line[5])]
                        },
                        1
                    )

                # Sector delimiter...
                elif line[0] == 'DELIMITER':
                    out_wr.write_row(line)

                line = sites.read_line()

            # Creating antennas information dataframe.
            
            self._antennas = pd.DataFrame(antennas_dict)

    def _associate_read(self, assoc_file: str):

        """PRIVATE METHOD which calculate the association between group of measurement points with

        sames EARFCNS/PCIS and base stations."""

        # XLXLXLXL
        # Associations between antennas and EARFCNs / PCIs, CAREFUL: should be the same as for _associate_data
        self._assocs = {'Cartoradio_Number': [], 'Ant_Number': [], 'TAC': [], 'CID': [], 'EARFCN': [], 'PCI': [],
                        'Score': []}
        self._assocDataFrame = pd.read_csv(assoc_file, sep='|')  # read the csv file (cevcafxxx.csv)
                                                                # and put it in a data frame

        self._EarfcnPciPair = self._measure_point[['EARFCN', 'PCI']]  # on ne garde que colonnes EARFCN et PCI
        df1 = self._EarfcnPciPair.drop_duplicates(subset=['EARFCN', 'PCI'])   # on retire les duplicatas
                                           # on a une dataframe avec tous les couples (EARFCN, PCI) differents

        # Pour chaque couple (EARFCN, PCI)
        for index1, row1 in df1.iterrows():
            for index2, row2 in self._assocDataFrame.iterrows():
                if ((row1["EARFCN"] == row2["EARFCN"]) and (row1["PCI"] == row2["PCI"])):
                    insert_data(self._assocs, {
                        'Cartoradio_Number': [self._assocDataFrame['Cartoradio_Number'][index2]],
                        'Ant_Number': [self._assocDataFrame['Ant_Number'][index2]],
                        'TAC': [self._assocDataFrame['TAC'][index2]],
                        'CID': [self._assocDataFrame['CID'][index2]],
                        'EARFCN': [self._assocDataFrame['EARFCN'][index2]],
                        'PCI': [self._assocDataFrame['PCI'][index2]],
                        'Score': [self._assocDataFrame['Score'][index2]]
                    }, 1)
                    #print('Found : Ant_number=', self._assocDataFrame['Ant_Number'][index2], '   (EARFCN,PCI)=(', self._assocDataFrame['EARFCN'][index2], ',',
                    #      self._assocDataFrame['PCI'][index2], ')  score=', self._assocDataFrame['Score'][index2])
                    print("+",end = '')

                    # print("===== PAIRE TROUVEE : =====")
                    # print(df1[df1.index == index1])
                    # print(self._assocDataFrame[self._assocDataFrame.index == index2])

    def _associate_data(self, MIN_NUMBER_OF_MEASURES_FOR_ASSOCIATION=50, allowed_ep: set[tuple] | None = None):

        """PRIVATE METHOD which calculate the association between group of measurement points with

        sames EARFCNS/PCIS and base stations."""

        # Associations between antennas and EARFCNs / PCIs
        self._assocsProp = {'Cartoradio_Number': [], 'Ant_Number': [], 'TAC': [], 'CID': [], 'EARFCN': [], 'PCI': [], 'Score': []}
        self._assocs =  {'Cartoradio_Number': [], 'Ant_Number': [], 'TAC': [], 'CID': [], 'EARFCN': [], 'PCI': [], 'Score': []}

        # Calculating Voronoi cells.

        # Base stations coordinates.
        bs_coords = np.array(list(self._antennas.groupby(['Lat', 'Lng']).groups.keys()))

        # Voronoi cells calculation.
        vor = sp.Voronoi(bs_coords)

        # Association between Voronoi cells and base stations coordinates.
        bs_vor = {'Lat': [], 'Lng': [], 'Vor': []}

        # Associating Voronoi cells and base stations coords...
        for i in range(len(vor.points)):
            point = vor.points[i]
            p_reg = vor.point_region[i]
            region = vor.regions[p_reg]

            # Filtering open Voronoi cells (at extremities of the covered area).
            if -1 not in region and region:
                insert_data(bs_vor, {
                    'Lat': [point[0]],
                    'Lng': [point[1]],
                    'Vor': [p_reg]
                }, 1)

        # Associating antennas and Voronoi cells.
        ant_vor_sectors = pd.merge(self._antennas, pd.DataFrame(bs_vor), on=['Lat', 'Lng']).drop_duplicates(
            ['Cartoradio_Number', 'Ant_Number'])

        # Calculating convex hulls.
        point_groups = self._measure_point.groupby(['TAC','CID','EARFCN','PCI'])
        gr_keys = point_groups.groups.keys()
        # filtre amont
        if allowed_ep:
            allowed = allowed_ep
            gr_keys = [k for k in gr_keys if (int(k[2]), int(k[3])) in allowed]

        groups = {}     # Groups of points of same EARFCN / PCI.
        hulls = {}      # Convex hulls associated to groups of points.

        # Calculating convex hulls...
        gr_keys = point_groups.groups.keys()

        for gr_key in gr_keys:
            gr = point_groups.get_group(gr_key)
            coords = np.array(list(zip(gr['Lat'], gr['Lng'])))
            groups[gr_key] = coords
            hulls[gr_key] = geom.MultiPoint(coords).convex_hull

        # Vectorizing criteria calculation functions...
        v_weight = np.vectorize(weight)     # Weight of each point.
        v_sigma = np.vectorize(calc_sigma)  # Angular criteria ("sigma")
        v_psi = np.vectorize(lambda x: 1.0 if x else 0.0)   # Cell criteria ("psi")
        v_belongs = np.vectorize(lambda x, y, s: s.contains(geom.Point(x, y)))    # "Belongs to shape" function.
        v_valid = np.vectorize(is_valid)    # "Theta" validity function (antenna selection).

        # Grouping antennas by Voronoi cell number.
        vor_groups = ant_vor_sectors.groupby(['Vor'])

        # For each group of point with same EARFCN / PCI...

        print('looking for possible associations')

        for gr_key in gr_keys:      # n

            # "Theta" criteria values.
            theta_values = {}

            # Group of points and their RSRPs.
            point_group = point_groups.get_group(gr_key)
            points_rsrps = point_group['RSRP'].to_numpy()

            # Size of group.
            card = len(point_group)

            if card>MIN_NUMBER_OF_MEASURES_FOR_ASSOCIATION:  # if no enough measurement, don't try any association

                # Calculating weights...
                weights = v_weight(points_rsrps)

                totalweight = np.sum(weights)

                if (totalweight>10):

                    # For each Voronoi cell...
                    for vor_key in vor_groups.groups.keys():  # i
                        vgroup = vor_groups.get_group((vor_key,))  # Group of antennas in the Voronoi cell.
                        vlen = len(vgroup)  # Number of antennas in the Voronoi cell.
                        vgroup = vgroup.to_dict('list')

                        # Polygon of the Voronoi cell.
                        vor_shape = geom.Polygon(vor.vertices[vor.regions[vor_key]])

                        # Station / polygon distance calculation...
                        linear_vor = geom.LinearRing(vor_shape.exterior.coords)

                        # BS coords...
                        vlat = vgroup['Lat'][0]
                        vlng = vgroup['Lng'][0]

                        # Calculating angles between points of base station and north over flat earth projection.

                        # Points latitude / longitude...
                        points_lat = point_group['Lat'].to_numpy()
                        points_lng = point_group['Lng'].to_numpy()

                        # Points coordinates over flat earth projection.
                        dirs_north = (points_lat - vlat) * (np.pi / 180)
                        dirs_east = (points_lng - vlng) * (np.pi / 180) * np.cos(vlat / 180 * np.pi)

                        # Angles between north direction and point direction from the current base station.

                        # minus artan2 should be considered since the angles are CLOCKWISE for azimut

                        angles = np.arctan2(dirs_east, dirs_north)
                        distPoints = np.sqrt(dirs_east ** 2 + dirs_north ** 2)

                        # calcul d'un score prendant la distance
                        # principe : si la distance augmente, le signal diminue. On essaye de trouver un produit
                        # qui soit cosntant idéalement constant et on regarde l'inverse de l'indice de Jain
                        # valeur 1 : excellent
                        # valeur>1 : assez mauvais

                        distbis = 1+np.corrcoef(distPoints ** 3.3, np.exp(points_rsrps*np.log(10)/10) )[0][1]

                        # Calculate values only if Voronoi cell intersects with the convex hull
                        # of the current group of points.
                        if vor_shape.intersects(hulls[gr_key]):

                            # Is each point belonging to the cell ?
                            points_belongs = v_belongs(points_lat, points_lng, vor_shape)

                            for i in range(vlen):  # j

                                # Azimuth delimitation of the sector and conversion in radian
                                # between -Pi and Pi, Be careful angles are CLOCKWISE
                                az_min = vgroup['AzimuthMin'][i]* (np.pi / 180)
                                az_max = vgroup['AzimuthMax'][i]* (np.pi / 180)

                                        # Criteria calculation.

                                # Angular criteria "sigma".
                                sigma_vect = v_sigma(angles, weights, az_min, az_max)
                                sigma = np.sum(sigma_vect) / totalweight  # modification XLXLXL totalweight

                                # Cell belonging criteria "phi".
                                psi_vect = v_psi(points_belongs) * sigma_vect
                                psi = np.sum(psi_vect) / totalweight  # modification XLXLXL totalweight

                                # Theta criteria calculation.
                                theta = calc_theta(sigma, psi)

                                if not theta == 0.0:
                                    theta_values[
                                        (vgroup['Cartoradio_Number'][i], vgroup['Ant_Number'][i], distbis, gr_key)
                                    ] = theta

                    # If non-zero theta values have been calculated...
                    if theta_values:

                        # Choosing one max theta value.
                        theta_argmax = max(theta_values, key=lambda k: theta_values[k])
                        theta_max = theta_values[theta_argmax]

                        # Check for other max values, equals to the first max value.
                        theta_list = [k for k in theta_values.keys()]

                        # Other theta values.
                        theta_array = np.array([theta_values[k] for k in theta_values.keys()])

                        # Selecting antennas.
                        if theta_array.size > 0:

                            # Select valid antennas following theta values.
                            valids = v_valid(theta_max, theta_array, 0.08)

                            # If valid antennas found, choose the antenna with a minimal distance
                            # with the convex hull of the current group of points.
                            if np.all(valids):             # for one candidate theta is much higher than for the other

                                # Inserting data.
                                insert_data(self._assocsProp, {
                                    'Cartoradio_Number': [theta_argmax[0]],
                                    'Ant_Number': [theta_argmax[1]],
                                    'TAC': [theta_argmax[3][0]],
                                    'CID': [theta_argmax[3][1]],
                                    'EARFCN': [theta_argmax[3][2]],
                                    'PCI': [theta_argmax[3][3]],
                                    'Score': [theta_max]
                                }, 1)

                                print('Ant_number=', theta_argmax[1], '   (EARFCN,PCI)=(', theta_argmax[3][2], ',',
                                    theta_argmax[3][3], ')  v1score=',theta_max)

                            else:
                                min_dist = theta_argmax[2]
                                argmin_dist = 0

                                # Selecting minimal base station / convex hull distance.
                                for i, selected in enumerate(theta_list):
                                    dst = selected[2]

                                    if dst < min_dist:
                                        min_dist = dst
                                        argmin_dist = i

                                if (theta_argmax[2]/min_dist>1.5):

                                    insert_data(self._assocsProp, {
                                        'Cartoradio_Number': [theta_list[argmin_dist][0]],
                                        'Ant_Number': [theta_list[argmin_dist][1]],
                                        'TAC': [theta_list[argmin_dist][3][0]],
                                        'CID': [theta_list[argmin_dist][3][1]],
                                        'EARFCN': [theta_list[argmin_dist][3][2]],
                                        'PCI': [theta_list[argmin_dist][3][3]],
                                        'Score': [theta_array[argmin_dist]]
                                    }, 1)

                                    print('Ant_number=', theta_list[argmin_dist][1], '   (EARFCN,PCI)=(', theta_list[argmin_dist][3][2], ',',
                                          theta_list[argmin_dist][3][3],')  v1score=',theta_max, 'Rem : closest')

                                else:       # the ratio of distance is not large enough => choose the sector best theta value

                                    # Inserting data.

                                    insert_data(self._assocsProp, {
                                        'Cartoradio_Number': [theta_argmax[0]],
                                        'Ant_Number': [theta_argmax[1]],
                                        'TAC': [theta_argmax[3][0]],
                                        'CID': [theta_argmax[3][1]],
                                        'EARFCN': [theta_argmax[3][2]],
                                        'PCI': [theta_argmax[3][3]],
                                        'Score': [theta_max]
                                    }, 1)

                                    print('Ant_number=', theta_argmax[1], '   (EARFCN,PCI)=(', theta_argmax[3][2], ',',
                                          theta_argmax[3][3],')  v1score=',theta_max)

        # identification for each Ant Number of all measurement groups associated
        # selection of the group with the highest score
        # when score 1 is found, elimination because it means points are not enough spread in the cell
        # trick : non selected (i.e. duplicates) Antenna numbers are forced to 0
        # first step = reduce all scores equal to 1 that are generally due to not enough point

        for i in range(len(self._assocsProp['Ant_Number'])):
            NoteMax = self._assocsProp['Score'][i]

            if NoteMax == 1:  # score 1 is suspect => reduction of the score
                self._assocsProp['Score'][i] = NoteMax/3  # reduce the score

        for i in range(len(self._assocsProp['Ant_Number'])):
            for j in range(i + 1, len(self._assocsProp['Ant_Number'])):
                if self._assocsProp['Ant_Number'][j] != 0:
                    if self._assocsProp['Ant_Number'][j] == self._assocsProp['Ant_Number'][i]:  # meme numero d'antenne pour deux associations
                        if self._assocsProp['EARFCN'][j] == self._assocsProp['EARFCN'][i]:  # meme ARFCN => garder qu'un
                            if self._assocsProp['Score'][j] > NoteMax:
                                NoteMax = self._assocsProp['Score'][j]
                                self._assocsProp['Ant_Number'][i] = 0  # on force numero d'origine a 0 car doublon a ne pas considerer
                            else:
                                self._assocsProp['Ant_Number'][j] = 0  # on force numero a 0 car doublon a ne pas reconsiderer
                        else:  # differents codes ARFCN
                            if self._assocsProp['PCI'][j] == self._assocsProp['PCI'][i]:  # meme code PCI => renforce credibilite association
                                NoteMax = self._assocsProp['Score'][i] + self._assocsProp['Score'][j] - self._assocsProp['Score'][i] * self._assocsProp['Score'][j] # on force note de chacune a somme des notes
                                self._assocsProp['Score'][i] = NoteMax
                                self._assocsProp['Score'][j] = NoteMax
                            else:  # differents codes EARFCN et differents code PCI
                                if self._assocsProp['Score'][j] > NoteMax:  # nouveau cas augmente la note
                                    NoteMax = self._assocsProp['Score'][j]
                                    self._assocsProp['Ant_Number'][i] = 0  # on force numero d'origine a 0 car doublon a ne pas considerer
                                else:
                                    self._assocsProp['Ant_Number'][j] = 0  # on tient pas compte de la nouvelle (si precedente deja trouvee 2 fois, sa note cumulative est normalement superieure => choix majoritaire)

        # creation of the definitive list with only one association per antenna
        for i in range(len(self._assocsProp['Ant_Number'])):

                if self._assocsProp['Ant_Number'][i] != 0:

                    insert_data(self._assocs, {
                        'Cartoradio_Number': [self._assocsProp['Cartoradio_Number'][i]],
                        'Ant_Number': [self._assocsProp['Ant_Number'][i]],
                        'TAC': [self._assocsProp['TAC'][i]],
                        'CID': [self._assocsProp['CID'][i]],
                        'EARFCN':[self._assocsProp['EARFCN'][i]],
                        'PCI': [self._assocsProp['PCI'][i]],
                        'Score': [1-self._assocsProp['Score'][i]]
                    }, 1)

    
    def _associate_data_with_TA(self):
        """Associate EARFCN/PCI pairs to antennas using Timing Advance and Azimuth to choose antenna within selected site."""

        delta = 80  # Tolerance in meters
        alpha = 0.5 # Exponent for distance weighting
        margin = 5  # Margin in km for bounding box
        threshold = 6  # Minimum score to consider an association valid
        distance_threshold = 50  # Minimum distance in meters between two values to consider a couple earfcns/pcis
        fact_rayon_terre = np.pi/180*6371  # conversion lat/lon to meters on earth surface: with theta in radian, multiply by this factor to have the distance in kilometers
        K = 1.0 # Set a constant K for confidence score calculation to convert to a 0-1 scale

        # print(f"Using delta: {delta}, alpha: {alpha}, margin: {margin} km, threshold: {threshold}")
        if debug:
            init_csv_top3()

        # Initialize the associations dictionary
        self._assocs = {
            'Cartoradio_Number': [], 'Ant_Number': [], 'TAC': [], 'CID': [],
            'EARFCN': [], 'PCI': [], 'Score': []
        }

        confidence_by_pair = {}
        # coef1_counts = defaultdict(int)            # (earfcn, pci, site) -> count
        # total_meas_per_pair = defaultdict(int)     # (earfcn, pci) -> count
        # ratios_rows = []                            # sorties "tous sites"

        # Load measurement and antenna data
        df_meas = self._measure_point.copy()
        df_ant = self._antennas.copy()

        print("Start association with timing advance")
        # Check if necessary columns are present
        if 'TA' not in df_meas.columns:
            print("[WARNING] No TA column found in measurement data.")
            return

        # Check if azimuth is available in antenna data
        use_azimuth = 'Azimuth' in df_ant.columns

        # Drop rows without values in Lat, Lng, and TA
        df_meas = df_meas.dropna(subset=['Lat', 'Lng', 'TA'])

        # Grouping measurements by EARFCN and PCI
        grouped = df_meas.groupby(['EARFCN', 'PCI'])

        # Get unique EARFCNs and antennas
        unique_earfcns = df_meas['EARFCN'].dropna().unique()
        unique_antennas = df_ant[['Cartoradio_Number', 'Ant_Number']].drop_duplicates()

        # Create antenna keys with unique combinations of EARFCN, Cartoradio_Number, and Ant_Number
        antenna_keys = [
            (earfcn, row.Cartoradio_Number, row.Ant_Number)
            for earfcn in unique_earfcns
            for _, row in unique_antennas.iterrows()
        ]

        # Sort and convert antenna keys and PCI keys to integers
        pci_keys = sorted(df_meas['PCI'].dropna().unique())

        # Global bbox (no margin)
        lat_min_all = df_meas['Lat'].min()
        lat_max_all = df_meas['Lat'].max()
        lng_min_all = df_meas['Lng'].min()
        lng_max_all = df_meas['Lng'].max()

        # Area of the global rectangle
        dy_km_all = (lat_max_all - lat_min_all) * fact_rayon_terre
        dx_km_all = (lng_max_all - lng_min_all) * fact_rayon_terre * np.cos(np.radians((lat_min_all + lat_max_all) / 2))
        S_rect_all = abs(dx_km_all * dy_km_all * 1e6) #km² to m²

        # Sites in global rectangle
        sites_in_all = df_ant[
            (df_ant['Lat'] >= lat_min_all) & (df_ant['Lat'] <= lat_max_all) &
            (df_ant['Lng'] >= lng_min_all) & (df_ant['Lng'] <= lng_max_all)
        ]['Cartoradio_Number'].nunique() # Count unique antennas in the global rectangle

        # Calculate global distance based on the area and number of sites
        if sites_in_all != 0:
            S_cell_all = S_rect_all / (sites_in_all * 3.0)  # tri-sector
            D_global = np.sqrt(S_cell_all * 8.0 / (3.0 * np.sqrt(3.0)))
            margin = (D_global/1000)*2 # adjust margin to cell size
        else:
            D_global = -1.0  # No antennas found

        # Convert to integer juste for printing
        antenna_keys = [(int(e), int(s), int(a)) for (e, s, a) in antenna_keys] 
        pci_keys = [int(i) for i in pci_keys]

        # Create a score matrix will contain max score for each EARFCN/PCI pair and antenna
        score_matrix = np.zeros((len(pci_keys), len(antenna_keys)))

        # Loop through each group of measurements with same EARFCN and PCI
        for (earfcn, pci), sub_df in grouped:

            seen_sites = set()

            # Create table of coordinates for the measurements
            coords_xy = np.array([latlng_to_xy(lat, lng) for lat, lng in zip(sub_df['Lat'], sub_df['Lng'])])

            # Skip groups with less than 2 measurements
            if len(coords_xy) < 2:
                print(f"[WARNING ]{earfcn}/{pci} ignored because points are too close")
                continue 

            # Compute the maximum distance between points in the group
            max_distance = pdist(coords_xy).max() 

            # Calculate the confidence score based on the maximum distance and global distance
            N = len(coords_xy)
            if D_global > 0:
                confidence_score = np.exp(-K * max_distance * np.sqrt(N) / D_global)
                # print(f"Processing EARFCN={earfcn}, PCI={pci}, N={N}, max_distance={max_distance:.1f}m, confidence_score={confidence_score:.2f}")
            else:
                confidence_score = 1
                print("[WARNING] No antennas detected in perimeter")
            
            confidence_by_pair[(earfcn, int(pci))] = confidence_score

            # Skip groups where the maximum distance is below the threshold
            if max_distance < distance_threshold:
                print(f"[SKIP] Group EARFCN={earfcn}, PCI={pci} ignored (distance={max_distance:.1f}m, {len(sub_df)} measures)")
                continue

            # Initialize a dictionary to hold vote scores for each site
            vote_scores = {}

            # we store for EACH point a dict: site -> (score_ajt, score_cumule, ta, L, dist)
            points_buffer = []

            # Calculate the bounding box for the measurements: add a margin of 5 km
            lat_min, lat_max = sub_df['Lat'].min(), sub_df['Lat'].max()
            lng_min, lng_max = sub_df['Lng'].min(), sub_df['Lng'].max()
            margin_lat = margin / fact_rayon_terre
            margin_lng = margin / (fact_rayon_terre * np.cos(np.radians((lat_min + lat_max) / 2)))
            lat_min -= margin_lat
            lat_max += margin_lat
            lng_min -= margin_lng
            lng_max += margin_lng
            # print(f"Processing EARFCN: {earfcn}, PCI: {pci}, Bounding Box: ({lat_min}, {lng_min}) to ({lat_max}, {lng_max})")

            # Antennas within the bounding box
            nearby_ants = df_ant[
                (df_ant['Lat'] >= lat_min) & (df_ant['Lat'] <= lat_max) &
                (df_ant['Lng'] >= lng_min) & (df_ant['Lng'] <= lng_max)
            ]

            # Garder une seule antenne par site (ici : la première)
            nearby_sites = nearby_ants.drop_duplicates(subset="Cartoradio_Number")

            print(f"Found {len(nearby_sites)} sites in bounding box")

            # Convert antenna coordinates to cartesian coordinates
            ant_coords = np.array([latlng_to_xy(lat, lng) for lat, lng in zip(nearby_sites['Lat'], nearby_sites['Lng'])])

            # Save site IDs for scoring
            site_ids = nearby_sites['Cartoradio_Number'].values
            
            # current cumulative total per site while browsing the points
            cumul_courant = {int(s): 0.0 for s in site_ids}

            # Loop through each measurement in the group
            for _, meas in sub_df.iterrows():

                lat_m, lng_m, ta = meas['Lat'], meas['Lng'], meas['TA']
                try:
                    # Calculate the theorical distance to each antenna using Timing Advance
                    L = compute_distance_with_TA(ta, 'LTE')
                except:
                    continue

                # Compute the real distance of the terminal to each antenna
                x_m, y_m = latlng_to_xy(lat_m, lng_m) 
                dx = x_m - ant_coords[:, 0]
                dy = y_m - ant_coords[:, 1]
                distances = np.sqrt(dx**2 + dy**2)

                # Calculate coefficients
                coefs = compute_coefs(L, distances, delta, alpha)

                per_site_stats = {}  # dict for one point

                if debug:
                    for site, coef, dist in zip(site_ids, coefs, distances):
                        site = int(site)
                        c = float(coef)

                        # Update overall group total AND current total "after this point"
                        vote_scores[site] = vote_scores.get(site, 0.0) + c
                        cumul_courant[site] = cumul_courant.get(site, 0.0) + c

                        # we keep for this point: add (=c), cumul_apres, ta, L, dist
                        per_site_stats[site] = (c, cumul_courant[site], ta, L, dist)

                    # buffer the line at this point
                    points_buffer.append( (lat_m, lng_m, per_site_stats) )

                # Score by site with cartoradio number as key
                for idx, coef in enumerate(coefs):
                    site_key = site_ids[idx]
                    vote_scores[site_key] = vote_scores.get(site_key, 0) + coef

            if not vote_scores:
                continue

            # Select the site with the highest score
            # If multiple sites have the same score, the max function will return one of them
            selected_site, best_score = max(vote_scores.items(), key=lambda x: x[1])
            top3_sites = sorted(vote_scores.items(), key=lambda x: x[1], reverse=True)[1:3]
            top3_ids = [sid for sid, _ in top3_sites]
            best_sites = {}
            best_sites[selected_site] = best_score

            for sid in top3_ids:
                if vote_scores[sid] < best_score/2:
                    continue
                else:
                    best_sites[sid] = vote_scores[sid]

            if debug: 

                # writting CSV: one line per point, keeping only 3 sites
                for (lat_m, lng_m, per_site_stats) in points_buffer:
                    top3_data_for_point = []
                    for sid in top3_ids:
                        if sid in per_site_stats:
                            s_ajt, s_cum, ta, L, dist = per_site_stats[sid]
                            top3_data_for_point.append( (sid, dist, L, ta, s_ajt, s_cum) )
                        else:
                            # if point don't have site
                            top3_data_for_point.append( (sid, 0.0, 0.0, "", 0.0, 0.0) )

                    # write
                    log_top3_row(pci=int(pci), earfcn=int(earfcn),
                                lat=lat_m, lng=lng_m,
                                top3_data=top3_data_for_point)
                    
                
            if best_score < threshold:
                print(f"[WARNING] No suitable site found for EARFCN: {earfcn}, PCI: {pci} with score {best_score}.")
                continue
            
            for bsite in best_sites:
                # Among the antennas of the selected site, choose the one with the best azimuth match
                subset_site = nearby_ants[nearby_ants['Cartoradio_Number'] == bsite]
                if subset_site.empty:
                    continue

                if use_azimuth:
                    # Average latitude and longitude of the measurements for bearing calculation
                    lat_cible = sub_df['Lat'].mean()
                    lng_cible = sub_df['Lng'].mean()

                    # Compute bearings from the antennas to the average measurement point
                    # and compare with azimuths to find the best match
                    bearings = compute_bearing(
                        subset_site['Lat'].values,
                        subset_site['Lng'].values,
                        lat_cible,
                        lng_cible
                    )

                    # Convert azimuths to bearings
                    azis = subset_site['Azimuth'].values
                    diffs = np.abs((bearings - azis + 180) % 360 - 180)
                    best_idx = np.argmin(diffs)

                else:
                    # When azimuth is not used, select the first antenna
                    best_idx = 0

                # Data for the best antenna
                best_ant = subset_site.iloc[best_idx]
                sample = sub_df.iloc[0]

                # Insertion dans _assocs
                self._assocs['Cartoradio_Number'].append(best_ant['Cartoradio_Number'])
                self._assocs['Ant_Number'].append(best_ant['Ant_Number'])
                self._assocs['TAC'].append(int(sample.get('TAC', 0)))
                self._assocs['CID'].append(int(sample.get('CID', 0)))
                self._assocs['EARFCN'].append(earfcn)
                self._assocs['PCI'].append(pci)
                self._assocs['Score'].append(confidence_by_pair.get((earfcn, pci), np.nan))

                print(f"Association found: EARFCN: {earfcn}, PCI: {pci}, Cartoradio number: {best_ant['Cartoradio_Number']}, Antenne: {best_ant['Ant_Number']}, Score: {confidence_by_pair.get((earfcn, pci), np.nan)}")
        print("End of association with timing advance")



    def _write_output(self, out_wr,  keep_only_keys: set[tuple] | None = None):

        """PRIVATE METHOD which writes relation calculated by _associate_datas in the output file.

        Produced fields are :
            - POINT: corresponds to a measurement point.
            - BS_ANT_DIR: describes the directivity of an antenna.
            - ASSOC: describe an association between an antenna and an EARFCN / PCI.

        Parameters:
            out_wr: output file.
        """
        # BS_ANT_DIR
        ants = self._antennas.groupby(['Ant_Number'])
        print(self._antennas)
        for a in ants.groups.keys():
            ant = ants.get_group((a,)).to_dict('list')
            out_wr.write_row([
                'BS_ANT_DIR', ant['Cartoradio_Number'][0], ant['Ant_Number'][0], ant['Lat'][0],
                ant['Lng'][0], ant['Dest_Lat'][0], ant['Dest_Lng'][0], ant['Height'][0]
            ])
        # ASSOC
        A = self._assocs
        for i in range(len(A['Cartoradio_Number'])):
            key = (
                to_int_token(A['Cartoradio_Number'][i]),
                to_int_token(A['Ant_Number'][i]),
                to_int_token(A['TAC'][i]),
                to_int_token(A['CID'][i]),
                to_int_token(A['EARFCN'][i]),
                to_int_token(A['PCI'][i]),
            )
            if keep_only_keys and key not in keep_only_keys:
                continue
            out_wr.write_row([
                'ASSOC', A['Cartoradio_Number'][i], A['Ant_Number'][i], A['TAC'][i],
                A['CID'][i], A['EARFCN'][i], A['PCI'][i], A['Score'][i], 28
            ])
        # MEASURE_SERVING
        P = self._measure_point.to_dict('list')
        for i in range(len(P['Lat'])):
            out_wr.write_row([
                'MEASURE_SERVING', P['Lat'][i], P['Lng'][i], P['TAC'][i],
                P['CID'][i], P['EARFCN'][i], P['PCI'][i], P['BEAM'][i],
                P['RSRP'][i], P['RSRQ'][i], P['RSSI'][i], P['CINR'][i]
            ])

def weight(rsrp: float) -> float:

    """Calculate the weight of a point using its RSRP.


    Parameters:

        rsrp: RSRP value of the point.


    Returns:

        Weight of the point, which is 0.15 if the RSRP is lesser than or equal to -100 dBm, 0.6 if the RSRP is between

        -100 dBm and -80 dBm, or 1.0 if the RSRP is greater than or equal to -80 dBm.

    """

    #if rsrp <= -100:

    #    return 0.15

    #elif -100 < rsrp < -80:

    #    return 0.6

    #else:

    #    return 1.0

    return 1/(1+math.exp((-95-rsrp)*0.15))

    #return 1/(1+math.exp((-90-rsrp)*0.22))

def calc_sigma(a: float, w: float, az_min: float, az_max: float):

    """Calculates the "sigma" angular indicator of one measurement point, angles should be in radian


    Parameters:

        a: angle between the north direction and the point direction over flat earth projection.

        w: weight of the point.

        az_min: minimum azimuth of the sector.

        az_max: maximum azimuth of the sector.


    Returns:

        the weight of the point if a is between az_min and az_max, 0.0 otherwise.

    """

    if a>4*np.pi or  az_min>4*np.pi or  az_max>4*np.pi:

        print("possible bug in calc_sigma calc, some angles are in degree not in radio")

    a = a % (2*np.pi)       # set all angles between 0 and 2Pi

    az_min = az_min % (2 * np.pi)

    az_max = az_max % (2 * np.pi)

    if az_min<az_max:

        return w if az_min < a < az_max else 0.0

    elif az_min>az_max:

        return w if a>az_min or a< az_max else 0.0

    else:

        return w    #if az_min==az_max this means an omnidirect antenna => always in the sector

def calc_theta(sigma: float, psi: float) -> float:

    """Calculate the "theta" indicator of a point from its sigma and psi values.


    Parameters:

        sigma: "sigma" angular indicator of the point.

        psi: "psi" cell belonging indicator of the point.


    Returns:

        theta, where theta = 0.8 * sigma + 0.2 * psi, if theta < 0.25, returns 0.0 otherwise.

    """

    return 0.0 if psi < 0.1 else (0.8 * sigma + 0.2 * psi)

def belongs(x: float, y: float, shape: geom.Polygon) -> bool:

    """Indicates if a point of given coordinates belongs to a given polygon.


    Parameters:

        x: x coordinate of the point.

        y: y coordinate of the point.

        shape: polygon.


    Returns:

        True if the point (x, y) belongs to the shape, False otherwise.

    """

    return shape.contains(geom.Point(x, y))

def is_valid(theta_max: float, other_theta: float, threshold: float):

    """Calculate the validity criteria for antenna selection for a given group of theta value, if all outputs are true, there is only one possible association, if an output is false .


    Parameters:

        theta_max: max theta value calculated with the group.

        other_theta: other theta value.

        threshold: threshold of selection.


    Returns:

        True if |log10(other_theta / theta_max)| > threshold or if theta_max = 0.0,

        or if other_theta / theta_max = 0.0 or ig theta_max = other_theta, False otherwise.

    """

    if theta_max == 0.0 or other_theta / theta_max == 0.0 or theta_max == other_theta:

        return True

    else:

        #        return other_theta > 0.8     # XL XL XL

        return np.abs(np.log10(other_theta / theta_max)) > threshold
    
def latlng_to_xy(lat, lng, R= 6371000):
    x = math.radians(lng) * R * math.cos(math.radians(lat))
    y = math.radians(lat) * R
    return x, y

def compute_bearing(lat1, lon1, lat2, lon2):
    """Compute the absolute bearing (in degrees) from point A (lat1, lon1) to point B (lat2, lon2)."""
    d_lon = np.radians(lon2 - lon1)
    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    x = np.sin(d_lon) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(d_lon))
    bearing = np.arctan2(x, y)
    return (np.degrees(bearing) + 360) % 360  # Normalize to [0, 360)

def compute_coefs(L, distances, delta, alpha):
    """Compute coefficients  based on the distance and delta
        If the antenna is inside the ring then the coefficient is one and the further 
        the antenna is from the ring defined by the calculated L +/- delta the smaller 
        the coefficient is"""
    with np.errstate(divide='ignore', invalid='ignore'):
        error = L - distances - delta/2
        coefs = np.where(
            error == 0,  # Perfect match
            1,
            np.minimum(1, (np.abs(delta / error) / 2) ** alpha)
        )
        coefs[np.isnan(coefs)] = 0
    return coefs

def compute_distance_with_TA(ta, techno):
    """Compute the distance in meters from the Timing Advance value.
        Multiply by 0.5208 to convert TA to meters (assuming 300 km/s speed of light)
        and divide by 2 to get the one-way distance"""
    if techno == 'LTE':
        return (ta * 0.5208 * 300) / 2
    elif techno == 'NR':
        return
    
def to_int_token(x: str) -> int:
    s = str(x).strip()
    if s in ("", "NA"):
        raise ValueError(f"Empty integer field or NA: {x!r}")
    try:
        return int(s)
    except ValueError:
        try:
            return int(round(float(s)))
        except ValueError:
            if "." in s and s.split(".", 1)[0].isdigit():
                return int(s.split(".", 1)[0])
            raise
    
class _NullWriter:
    def write_row(self, _): pass  # no-op pour réutiliser _read_* sans fichier