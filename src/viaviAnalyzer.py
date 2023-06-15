import datetime
import time
import pandas as pd
import glob
import viaviparser
from src import csvtools, freq_conversion
from src.freq_conversion import conv


class Viavilyzer:

    """Take the path of CSV files, merge all the CSV files and create a single CSV file"""
    def merge(path: str):
        files = glob.glob(path + "*.csv")
        data = []
        for file in files:
            df = pd.read_csv(file, dtype=str)
            data.append(df)

        merge = pd.concat(data)
        merge.to_csv(path + 'merge.csv', index=False)

    """Convert time string column of a csv file into timestamp and return dataframe with a new column 'Timestamp' 
    instead 'Date' and 'Time' """
    def time_stamp(filename):
        dtype_mapping = {
            'Date': str,
            'Time': str,
            'Latitude': float,
            'Longitude': float,
            'Center Frequency (MHz)': float,
            'Technology (5G NR LTE FDD LTE TDD)': str,
            'PCI': int,
            'SSB Index': int,
            'S-SS RSRP / RSRP (dBm)': float,
            'S-SS RSRQ / RSRQ (dB)': float,
            'S-SS SINR / RS SINR (dB)': float,
            'S-SS RSSI / S-SS RSSI (dBm)': float,
            'Time Error (us)': float,
            'Timestamp': float
        }
        data = pd.read_csv(filename)
        date = data['Date'][0]
        data = data[(data['PCI'] != '--') & (data['SSB Index'] != '--')  & (data['Center Frequency (MHz)'] != '--')].reset_index(drop=True)
        start = time.mktime(datetime.datetime.strptime(((data['Time'][0]).split("CET")[0]).replace(" ", ""),
                                                       "%H:%M:%S.%f%p").timetuple())
        data.insert(0, 'Timestamp', 0.0)
        data = data.astype(dtype_mapping)
        for index, row in data.iterrows():
            x = abs(start - time.mktime(datetime.datetime.strptime(((row['Time']).split("CET")[0]).replace(" ",""),
                                                                     "%H:%M:%S.%f%p").timetuple()))
            data.loc[index, 'Timestamp'] = x
        data = data.drop(['Date', 'Time'], axis=1)
        return data, date

    """ List all the tuples (arfcn, pci, beam_index) of a csv file and their number of measurements """
    def read_measures(filename):
        data, date = Viavilyzer.time_stamp(filename)
        tuples = Viavilyzer.earfcn_pci_beam(data)
        l = list(tuples)
        occs = [0] * len(l)
        techno = data['Technology (5G NR LTE FDD LTE TDD)'][0]
        for index, row in data.iterrows():
            arfcn = conv.freq_to_arfcn(row['Center Frequency (MHz)'])
            pci = row['PCI']
            beam_index = row['SSB Index']
            occs[l.index((arfcn, pci, beam_index))] += 1
        return l, occs, techno, date, data

    """ Return a set of tuples (arfcn, pci, beam_index) from a dataframe"""
    def earfcn_pci_beam(df):
        arfcns = []
        pcis = []
        beam_indexes = []
        for index, row in df.iterrows():
            arfcns.append(conv.freq_to_arfcn(row['Center Frequency (MHz)']))
            pcis.append(row['PCI'])
            beam_indexes.append(row['SSB Index'])
        return set(zip(arfcns, pcis, beam_indexes))

    """Return the row of the serving PCI between two timestamps """
    def get_best_pci(min, max, df):
        sub_df = df[(df['Timestamp'] >= min) & (df['Timestamp'] < max)]
        tuples = Viavilyzer.earfcn_pci_beam(sub_df)
        for t in tuples:
            freq = t[0]
            pci = t[1]
            ssb_index = t[2]
            max_rsrp = -150.0
            max_row = None
            current_measurements = [0.0] * len(tuples)
            for index, row in sub_df.iterrows():
                if row['PCI'] == pci and conv.freq_to_arfcn(row['Center Frequency (MHz)']) == freq and row['SSB Index'] == ssb_index:
                    current_measurements.append(conv.dbm_to_watt(row['S-SS RSRP / RSRP (dBm)']))
            total = 0.0
            for x in current_measurements:
                total+=x
            mean = total/len(current_measurements)
            if max_rsrp < mean:
                max_rsrp = mean
                max_row = row
                #max_row['S-SS RSRP / RSRP (dBm)'] = max_rsrp
        return max_row

    """Produce a measurement file"""
    def produce_csv_file(filename):
        l, occs, techno, date, data = Viavilyzer.read_measures(filename)
        csv_header = {
            'VERSION': ['Version'],
            'DATE': ['Date'],
            'TECHNO': ['Techno'],
            'MEAS_EARFCNS': ['NA', 'NA', 'NA', 'NA', 'EARFCN1', 'EARFCN2', 'EARFCN3', 'etc'],
            'MEAS_PCIS': ['NA', 'NA', 'NA', 'NA', 'PCI1', 'PCI2', 'PCI3', 'etc'],
            'MEAS_BEAMS': ['NA', 'NA', 'NA', 'NA', 'BEAM1', 'BEAM2', 'BEAM3', 'etc'],
            'MEAS_NB': ['NA', 'NA', 'NA', 'NA', 'nb_meas_for_1', 'nb_meas_for_2', 'nb_meas_for_3', 'etc'],
            'CELLINFO': ['Timestamp', 'Lat', 'Lng', 'EARFCN', 'PCI', 'TAC', 'CID', 'MCC', 'MNC'],
            'MEASURE_SERVING': [
                'Timestamp', 'Lat', 'Lng', 'Serving_EARFCN', 'Serving_PCI',
                'Serving_RSRP', 'Serving_RSRQ', 'Serving_RSSI', 'Serving_CINR', 'Time_error'
            ],
            'MEASUREMENT': ['Timestamp', 'Lat', 'Lng', 'Measurement_Name', 'Values']
        }
        # tous les 5 secondes
        min = 0
        max = 5
        end = int(round(data['Timestamp'][len(data)-1]))

        with csvtools.CSVWriter('csv_tmp.csv', csv_header) as csv_out:
            csv_out.write_row(['VERSION'] + ['2.0'])
            csv_out.write_row(['DATE'] + [date])
            csv_out.write_row(['TECHNO'] + [techno])
            csv_out.write_row(['MEAS_EARFCNS'] + [''] * 4 + [epb[0] for epb in l])
            csv_out.write_row(['MEAS_PCIS'] + [''] * 4 + [epb[1] for epb in l])
            csv_out.write_row(['MEAS_BEAMS'] + [''] * 4 + [epb[2] for epb in l])
            csv_out.write_row(['MEAS_NB'] + [''] * 4 + [occs[l.index(epb)] for epb in l])

            serving_pci = -1
            for i in range(0, end, 5):
                x = Viavilyzer.get_best_pci(min, max, data)
                if serving_pci != x['PCI']:
                    csv_out.write_row(['CELLINFO'] + [x['Timestamp']] + [x['Latitude']] + [x['Longitude']] + [x['Center Frequency (MHz)']] + [x['PCI']] + [x['PCI']])
                serving_pci = x['PCI']
                csv_out.write_row(['MEASURE_SERVING'] + [x['Timestamp']] + [x['Latitude']] + [x['Longitude']] + [x['Center Frequency (MHz)']] + [x['PCI']] + [x['S-SS RSRP / RSRP (dBm)']] + [x['S-SS RSRQ / RSRQ (dB)']] + [x['S-SS RSSI / S-SS RSSI (dBm)']] + [x['S-SS SINR / RS SINR (dB)']] + [x['Time Error (us)']])
                sub_df = data[(data['Timestamp'] >= min) & (data['Timestamp'] < max) & (data['PCI'] != serving_pci)]
                min+=5
                max+=5
                """
                for m in sub_df:
                    csv_out.write_row(['MEASUREMENT'] + [m['Timestamp']] + [m['Latitude']] + [m['Longitude']] )
                """
# Tests
fields = ['Date', 'Time', 'Latitude', 'Longitude', 'Center Frequency', 'Technology', 'PCI', 'SSB Index',
          'S-SS RSRP',
          'S-SS RSSI', 'S-SS RSRQ', 'S-SS SINR', 'Time Error']
#Viavilyzer.merge("test_files/")

#tuples = Viavilyzer.earfcn_pci_beam("test_files/merge.csv")
#print(tuples)

# Read the columns names of a file
#colsnames = viaviparser.columns_names("test_files/merge.csv")
#dic = viaviparser.dic_viavi(fields, colsnames)


Viavilyzer.produce_csv_file("test_files/Save_longchamps_221222161029.csv")