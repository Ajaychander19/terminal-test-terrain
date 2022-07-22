"""This module contains functions used to process Cartoradio files."""

from dictutils import insert_data

import numpy as np
import pandas as pd

import csvtools

import math


def process_cartoradio(sitefile_path: str, antfile_path: str, output_dir: str):
    """Processes Cartoradio files.

    Cartoradio files processing takes two input files, typically named "Sites_Cartoradio" and
    "Antennes_Emetteurs_Frequences_Cartoradio", which contain respectively base station geolocation, and base station
    antennas, frequencies, directivity.

    The function uses only directive LTE antennas, and produce in the output file information about the antennas and the
    delimitation of their sectors. Data are produced in a CSV-like format based on the Accuver Open Format.

    Parameters:
        sitefile_path: path of the "Sites" file.
        antfile_path: path of the "Antennas" file.
        output_dir: path of the output file.
    """

    # Initial CSV import
    print('Reading {} data...'.format(sitefile_path), end=' ')
    sitesdf = pd.read_csv(sitefile_path, sep=';', encoding='ISO-8859-1')
    print('read.')
    print('Reading {} data...'.format(antfile_path), end=' ')
    antdf = pd.read_csv(antfile_path, sep=';', encoding='ISO-8859-1')
    print('read.')

    print('Preparing data...', end=' ')

    # Join between sitesdf and antdf
    siteant = pd.merge(sitesdf, antdf, left_on='Numéro du support', right_on='Numéro de support')

    # Projection over interesting fields.
    siteant = siteant[[
        'Numéro de support', 'Numéro Cartoradio', 'Numéro de Station',
        'Exploitant', "Numéro d'antenne", 'Directivité', 'Azimut', 'Système',
        'Latitude', 'Longitude', 'Hauteur / sol', 'Adresse', 'Commune', 'Début',
        'Fin', 'Unité'
    ]]

    print('done.')

    # Removing useless entries, keeping only directive LTE antennas.
    siteant = siteant[is_system_valid(siteant['Système']) & (siteant['Directivité'] == 'Directif')]

    # Grouping by operators.
    op_groups = siteant.groupby('Exploitant')

    # Output CSV file header
    header = {
        'BS_ANTENNA': [
            'Support_Number', 'Cartoradio_Number', 'Lat', 'Lng', 'Height', 'Info_Addr', 'Info_Municipality',
            'Ant_Number', 'Dest_Lat', 'Dest_Lng', 'Azimuth', 'AzimuthMin', 'AzimuthMax', 'MinFreq', 'MaxFreq'
        ],
        'DELIMITER': ['Cartoradio_Number', 'Support_Lat', 'Support_Lng', 'Del_Lat', 'Del_Lng']
    }

    # Reading input data by operator.
    for op in op_groups.groups.keys():

        print('Operator {}.'.format(op))

        # Opening sites and rejected file.
        with csvtools.CSVWriter('{0}/sites_{1}.csv'.format(output_dir, op), header) as out_file, \
                csvtools.CSVWriter('{0}/rejected_{1}.csv'.format(output_dir, op), header) as rej_file:

            # Dataset of the current operator
            op_group = op_groups.get_group(op)

            # Grouping by base station.
            station_groups = op_group.groupby('Numéro de support')

            # For each base station found...
            for sta in station_groups.groups.keys():

                # Sorting values per azimut.
                station_group = station_groups.get_group(sta).sort_values('Azimut')

                # Azimuths series.
                azimuths = station_group['Azimut'].drop_duplicates().reset_index(drop=True)
                az_count = len(azimuths)

                # Converting station data into a dictionary.
                station_group_dict = station_group.to_dict('list')

                # Choosing to keep or reject the station following if the station is underground or not.
                out = rej_file if station_group_dict['Hauteur / sol'][0] < 0 else out_file

                if station_group_dict['Hauteur / sol'][0] < 0:
                    print('Rejected base station {} (reason: underground).'.format(supp_num))

                # Delimitation lines of sectors.
                delimiters = {'carto_num': [], 'lat': [], 'lng': [], 'del_lat': [], 'del_lng': []}

                # Associates antennas azimuths and sectors delimiters azimuths.
                az_assoc = {}

                # Last calculated maximum azimuth of a sector.
                last_az_max = 0
                az_min_zero = 0

                # Max and min azimuths of current sector delimiters
                az_min, az_max = None, None

                # For each azimuth found for this base station...
                for i in range(az_count):

                    curr_az = azimuths[i]   # Current azimuth.

                    if az_count == 1:
                        # If there is only one antenna, we suppose that antenna covers a 120° sector.
                        az_min = curr_az - 60
                        az_max = curr_az + 60
                    elif az_count > 1 and i == az_count - 1:
                        # If the current azimuth is the last one, extending the angle of the current sector
                        # to the first sector.
                        az_min = last_az_max
                        az_max = az_min_zero + 360
                    elif az_count > 1 and i == 0:
                        az_min = min(
                            (curr_az + azimuths[az_count - 1] - 360) / 2,
                            (curr_az + azimuths[i + 1]) / 2
                        )
                        az_max = max(
                            (curr_az + azimuths[az_count - 1] - 360) / 2,
                            (curr_az + azimuths[i + 1]) / 2
                        )
                        az_min_zero = az_min
                    elif az_count > 1 and i > 0:
                        az_min = min((curr_az + azimuths[i - 1]) / 2, (curr_az + azimuths[i + 1]) / 2)
                        az_max = max((curr_az + azimuths[i - 1]) / 2, (curr_az + azimuths[i + 1]) / 2)

                    last_az_max = az_max

                    # Adding association between azimuth min and max.
                    az_assoc[curr_az] = (az_min, az_max)

                # Azimuths of delimiters already inserted in the output file.
                az_delimited = []

                # Inserting data in the output file...
                for i in range(len(station_group_dict['Numéro Cartoradio'])):

                    # Current Cartoradio Number.
                    carto_num = station_group_dict['Numéro Cartoradio'][i]

                    # Current antenna azimuth.
                    ant_az = station_group_dict['Azimut'][i]

                    # Number of the antenna support.
                    supp_num = station_group_dict['Numéro de support'][i]

                    # Geolocation of the antenna.
                    lat = station_group_dict['Latitude'][i]
                    lng = station_group_dict['Longitude'][i]

                    # Azimuths of the delimiters of the antenna sector
                    ant_az_min = az_assoc[ant_az][0]
                    ant_az_max = az_assoc[ant_az][1]

                    # Frequency band of the antenna.
                    freq_unit = station_group_dict['Unité'][i]
                    beg_freq = calculate_freq(station_group_dict['Début'][i], freq_unit)
                    end_freq = calculate_freq(station_group_dict['Fin'][i], freq_unit)

                    # Writing BS_ANTENNA entry...
                    out.write_row([
                        'BS_ANTENNA', supp_num, carto_num,
                        lat, lng, station_group_dict['Hauteur / sol'][i], station_group_dict['Adresse'][i],
                        station_group_dict['Commune'][i], station_group_dict["Numéro d'antenne"][i],
                        lat + 0.0005 * math.cos(ant_az * np.pi / 180),
                        lng + 0.0005 * math.sin(ant_az * np.pi / 180),
                        ant_az, ant_az_min, ant_az_max, beg_freq, end_freq
                    ])

                    # Inserting delimiters to write in the file if they
                    # had not been inserted yet.

                    if ant_az_min % 360 not in az_delimited:
                        az_delimited.append(ant_az_min % 360)
                        del_coords = calculate_delimiters(lat, lng, ant_az_min)
                        insert_data(
                            delimiters,
                            {
                                'carto_num': [carto_num],
                                'lat': [lat],
                                'lng': [lng],
                                'del_lat': [del_coords[0]],
                                'del_lng': [del_coords[1]]
                            },
                            1
                        )

                    if ant_az_max % 360 not in az_delimited:
                        az_delimited.append(ant_az_max % 360)
                        del_coords = calculate_delimiters(lat, lng, ant_az_max)
                        insert_data(
                            delimiters,
                            {
                                'carto_num': [carto_num],
                                'lat': [lat],
                                'lng': [lng],
                                'del_lat': [del_coords[0]],
                                'del_lng': [del_coords[1]]
                            },
                            1
                        )

                # Writing delimiters.
                for i in range(len(delimiters['carto_num'])):
                    out.write_row(
                        ['DELIMITER', delimiters['carto_num'][i], delimiters['lat'][i],
                         delimiters['lng'][i], delimiters['del_lat'][i], delimiters['del_lng'][i]]
                    )

        print('Done for {}.'.format(op))

    print('Cartoradio processing done.')


def is_system_valid(ser: pd.Series) -> pd.Series:
    res = []
    for s in ser:
        res.append('LTE' in s)  # or '5G' in s
    return pd.Series(res)


def calculate_delimiters(lat: float, lng: float, azimuth: float) -> (float, float):
    return (
        lat + 0.3 * math.cos(azimuth * np.pi / 180),
        lng + 0.3 * math.sin(azimuth * np.pi / 180)
    )


def calculate_freq(val: float, unit: str) -> float:
    if unit == 'KHz':
        return val * 0.001
    elif unit == 'MHz':
        return val
    elif unit == 'GHz':
        return val * 1000.0
    else:
        raise ValueError('Invalid unit : {}.'.format(unit))
