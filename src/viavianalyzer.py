import datetime
import time
import os
import pandas as pd
import glob
from freq_conversion import conv
import csvtools

class Viavilyzer:

    def merge(path: str):
        """Take the path of CSV files, merge all the CSV files and create a single CSV file:

        Parameters
        ----------
        path : str
            Path of CSV files
        Returns
        -------
        list[str]
            List of files
        """
        files = glob.glob(path + "*.csv")
        data = []
        for file in files:
            df = pd.read_csv(file, dtype=str)
            data.append(df)

        merge = pd.concat(data)
        merge.to_csv(path + 'measurements_merge.csv', index=False)

    def seperate_op(filename, directory):
        """Separate measurements in different files for each operator

        Parameters
        ----------
        filename: str
        """
        df = pd.read_csv(filename)
        earfcn_list = df['Center Frequency (MHz)'].unique()

        files = []

        for earfcn in earfcn_list:
            df_earfcn = df[df['Center Frequency (MHz)'] == earfcn].reset_index(drop=True)
            x = str(conv.freq_to_arfcn(earfcn))
            name = os.path.basename(filename)
            nom_fichier = f"{directory}/{x}_{name}"
            df_earfcn.to_csv(nom_fichier)
            files += [nom_fichier]
        return files

    def totimestamp(filename: str, threshold: float):
        """Convert time string column of a CSV file into timestamp and return dataframe with a new column 'Timestamp'
         instead 'Date' and 'Time'

        Parameters
        ----------
        filename : str
            the path of the CSV file
        threshold : float
            threshold of RSRP PBCH
        Returns
        -------
        tuple
            (The dataframe, the date of the first measure)
         """
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
        data = data[(data['PCI'] != '--') & (data['SSB Index'] != '--') & (data['PBCH DM-RS RSRP (dBm) /'] != '--') & (
                    data['Center Frequency (MHz)'] != '--')].reset_index(drop=True)
        data = data[(data['PBCH DM-RS RSRP (dBm) /'].astype(float)) > threshold]
        start = time.mktime(datetime.datetime.strptime("2023"+((data['Time'][0]).split("CEST")[0]).replace(" ", ""),
                                                       "%Y%H:%M:%S.%f%p").timetuple())

        data.insert(0, 'Timestamp', 0.0)
        data = data.astype(dtype_mapping)
        time_zone = "CET"
        if "CEST" in data.iloc[0]['Time']:
            time_zone = "CEST"

        for index, row in data.iterrows():
            x = abs(time.mktime(datetime.datetime.strptime("2023"+((row['Time']).split(time_zone)[0]).replace(" ", ""),
                                                                   "%Y%H:%M:%S.%f%p").timetuple()) - start)
            data.loc[index, 'Timestamp'] = x
        data = data.drop(['Date', 'Time'], axis=1)
        return data, date

    def read_measures(filename: str, threshold):
        """ List all the tuples (arfcn, pci, beam_index) of a csv file and their number of measurements
        Parameters
        ----------
        filename : str
            the path of the CSV file
        threshold: float
            threshold of RSRP PBCH
        Returns
        -------
        tuple
            (The list of tuples(earfcn-beam-pci), their number of occurences, technology used, the date of the first measure,
            the dataframe)
        """
        data, date = Viavilyzer.totimestamp(filename, threshold)
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

    def earfcn_pci_beam(df):
        """ Return a set of tuples (arfcn, pci, beam_index) from a dataframe

        Parameters
        ----------
        df : str
            A dataframe

        Returns
        -------
        set
            set of different earfcn-pci-beam tuples
        """
        arfcns = []
        pcis = []
        beam_indexes = []
        for index, row in df.iterrows():
            arfcns.append(conv.freq_to_arfcn(row['Center Frequency (MHz)']))
            pcis.append(row['PCI'])
            beam_indexes.append(row['SSB Index'])
        return set(zip(arfcns, pcis, beam_indexes))

    def mean(df, unit):
        if len(df) > 0:
            total = 0.0
            for index, row in df.iterrows():
                total += conv.linearScale(row[unit])
            mean = total / len(df)
            return conv.dBscale(mean)
        return -500.0

    def get_best_pci(first, second, df):
        """Return the row of the serving PCI between two timestamps and the subdataframe of all measurements between
        Parameters
        ----------
        first:
            First timestamp
        second:
            Second timestamp
        Returns
        -------
        tuple
            (The row of the serving PCI, a subdataframe)
        """
        sub_df = df[(df['Timestamp'] >= first) & (df['Timestamp'] <= second)]
        copy = sub_df.copy()
        tuples = Viavilyzer.earfcn_pci_beam(sub_df)
        max_rsrp = -200.0
        max_row = None
        for t in tuples:
            pci = t[1]
            ssb_index = t[2]
            filtered_rows = copy[(copy['PCI'] == pci) & (copy['SSB Index'] == ssb_index)]
            mean_rsrp = Viavilyzer.mean(filtered_rows, 'S-SS RSRP / RSRP (dBm)')
            if max_rsrp < mean_rsrp and len(filtered_rows) > 0:
                max_rsrp = mean_rsrp
                max_row = filtered_rows.iloc[0].copy()
                max_row['Timestamp'] = second - 1
                max_row['S-SS RSRP / RSRP (dBm)'] = max_rsrp
                max_row['S-SS RSRQ / RSRQ (dB)'] = Viavilyzer.mean(filtered_rows, 'S-SS RSRQ / RSRQ (dB)')
                max_row['S-SS RSSI / S-SS RSSI (dBm)'] = Viavilyzer.mean(filtered_rows, 'S-SS RSSI / S-SS RSSI (dBm)')
                max_row['S-SS SINR / RS SINR (dB)'] = Viavilyzer.mean(filtered_rows, 'S-SS SINR / RS SINR (dB)')
        return max_row, sub_df

    def get_measurements(tuples, df):
        """ Return the measurements of a dataframe separated by categories (RSRQ, RSSI, RSRP)
        Parameters
        ----------
        start:
            First timestamp
        end:
            Second timestamp
        Returns
        -------
        tuple
            three categorie measurements lists: RSRQ, RSSI, RSRP
        """
        measurements_RSRQ = []
        measurements_RSSI = []
        measurements_RSRP = []
        for t in tuples:
            for index, row in df.iterrows():
                if row['PCI'] == t[1] and conv.freq_to_arfcn(row['Center Frequency (MHz)']) == t[0] and row[
                    'SSB Index'] == t[2]:
                    measurements_RSRQ += [row['S-SS RSRQ / RSRQ (dB)']]
                    measurements_RSSI += [row['S-SS RSSI / S-SS RSSI (dBm)']]
                    measurements_RSRP += [row['S-SS RSRP / RSRP (dBm)']]
                    #break
            measurements_RSRQ += ['']
            measurements_RSSI += ['']
            measurements_RSRP += ['']
        return measurements_RSRQ, measurements_RSSI, measurements_RSRP

    def produce_csv_file(filename, interval, threshold, directory):
        """Produce a measurement file
        Parameters
        ----------
        filename : str
            the path of the CSV file
        interval: int
            interval(seconds) to determinate the serving PCI
        threshold: float
            threshold of RSRP PBCH
        """
        l, occs, techno, date, data = Viavilyzer.read_measures(filename, threshold)
        n = len(l)

        csv_header = {
            'VERSION': ['Version'],
            'DATE': ['Date'],
            'TECHNO': ['Techno'],
            'MEAS_EARFCNS': ['NA', 'NA', 'NA', 'NA'],
            'MEAS_PCIS': ['NA', 'NA', 'NA', 'NA'],
            'MEAS_BEAMS': ['NA', 'NA', 'NA', 'NA'],
            'MEAS_NB': ['NA', 'NA', 'NA', 'NA'],
            'CELLINFO': ['Timestamp', 'Lat', 'Lng', 'EARFCN', 'PCI', 'TAC', 'CID', 'MCC', 'MNC'],
            'MEASURE_SERVING': [
                'Timestamp', 'Lat', 'Lng', 'Serving_EARFCN', 'Serving_PCI', 'Serving_BEAM',
                'Serving_RSRP', 'Serving_RSRQ', 'Serving_RSSI', 'Serving_CINR'
            ],
            'MEASUREMENT': ['Timestamp', 'Lat', 'Lng', 'Measurement_Name', 'Values']
        }

        csv_header['MEAS_EARFCNS'] = csv_header['MEAS_EARFCNS'] + ['EARFCN_{}'.format(i) for i in range(n)]
        csv_header['MEAS_PCIS'] = csv_header['MEAS_PCIS'] + ['PCI_{}'.format(i) for i in range(n)]
        csv_header['MEAS_BEAMS'] = csv_header['MEAS_BEAMS'] + ['BEAM_{}'.format(i) for i in range(n)]
        csv_header['MEAS_NB'] = csv_header['MEAS_NB'] + ['nb_meas_{}'.format(i) for i in range(n)]

        min = 0
        max = interval
        end = int(round(data['Timestamp'][len(data) - 1]))

        earfcn = str(conv.freq_to_arfcn(data['Center Frequency (MHz)'][0]))

        name = os.path.basename(filename)
        output_name = f'{directory}/cev_{name}'

        with csvtools.CSVWriter(output_name, csv_header) as csv_out:
            csv_out.write_row(['VERSION'] + ['2.0'])
            csv_out.write_row(['DATE'] + [date])
            csv_out.write_row(['TECHNO'] + [techno])
            csv_out.write_row(['MEAS_EARFCNS'] + [''] * 4 + [epb[0] for epb in l])
            csv_out.write_row(['MEAS_PCIS'] + [''] * 4 + [epb[1] for epb in l])
            csv_out.write_row(['MEAS_BEAMS'] + [''] * 4 + [epb[2] for epb in l])
            csv_out.write_row(['MEAS_NB'] + [''] * 4 + [occs[l.index(epb)] for epb in l])

            serving_pci = -1
            for i in range(0, end, interval):
                x, sub_df = Viavilyzer.get_best_pci(min, max, data)
                if x is None:
                    continue
                if serving_pci != x['PCI']:
                    csv_out.write_row(
                        ['CELLINFO'] + [x['Timestamp']] + [x['Latitude']] + [x['Longitude']] + [earfcn] + [x['PCI']] + [
                            '00'] + ['00'] + ['00'] + ['00'])
                    serving_pci = x['PCI']

                for j in range(min, max):
                    data_timestamp = sub_df[(sub_df['Timestamp'] == j)].reset_index(drop=True)
                    if len(data_timestamp) > 0:
                        t = data_timestamp.iloc[0]
                        measurements_RSRQ, measurements_RSSI, measurements_RSRP = Viavilyzer.get_measurements(l,
                                                                                                              data_timestamp)
                        csv_out.write_row(['MEASUREMENT'] + [t['Timestamp']] + [t['Latitude']] + [t['Longitude']] + [
                            'RSRP'] + measurements_RSRP)
                        csv_out.write_row(['MEASUREMENT'] + [t['Timestamp']] + [t['Latitude']] + [t['Longitude']] + [
                            'RSRQ'] + measurements_RSRQ)
                        csv_out.write_row(['MEASUREMENT'] + [t['Timestamp']] + [t['Latitude']] + [t['Longitude']] + [
                            'RSSI'] + measurements_RSSI)
                csv_out.write_row(['MEASURE_SERVING'] + [x['Timestamp']] + [x['Latitude']] + [x['Longitude']]
                                  + [earfcn] + [x['PCI']] + [x['SSB Index']] + [x['S-SS RSRP / RSRP (dBm)']]
                                  + [x['S-SS RSRQ / RSRQ (dB)']] + [x['S-SS RSSI / S-SS RSSI (dBm)']]
                                  + [x['S-SS SINR / RS SINR (dB)']])
                min += interval
                max += interval

    def produces_csv_op_files(filename, directory):
        files = Viavilyzer.seperate_op(filename, "../tmp")
        for f in files:
            Viavilyzer.produce_csv_file(f, 5, -150.0, directory)

        for f in os.listdir("../tmp"):
            path = os.path.join("../tmp", f)
            if os.path.isfile(path):
                os.remove(path)