from dictutils import insert_data

import numpy as np
import pandas as pd

import csvtools

import math


def process_cartoradio(sitefile_path: str, antfile_path: str, output_dir: str):

    # Initial CSV import
    sitesdf = pd.read_csv(sitefile_path, sep=';', encoding='ISO-8859-1')
    antdf = pd.read_csv(antfile_path, sep=';', encoding='ISO-8859-1')

    # Join between sitesdf and antdf
    siteant = pd.merge(sitesdf, antdf, left_on='Numéro du support', right_on='Numéro de support')

    # Projection over intersting fields.
    siteant = siteant[[
        'Numéro de support', 'Numéro Cartoradio', 'Numéro de Station',
        'Exploitant', "Numéro d'antenne", 'Directivité', 'Azimut', 'Système',
        'Latitude', 'Longitude', 'Hauteur / sol', 'Adresse', 'Commune', 'Début',
        'Fin', 'Unité'
    ]]

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
        'DELIMITER': ['Support_Number', 'Support_Lat', 'Support_Lng', 'Del_Lat', 'Del_Lng']
    }

    # Reading

    for op in op_groups.groups.keys():

        with csvtools.CSVWriter('{0}/sites_{1}.csv'.format(output_dir, op), header) as out_file, \
                csvtools.CSVWriter('{0}/rejected_{1}.csv'.format(output_dir, op), header) as rej_file:

            op_group = op_groups.get_group(op)
            station_groups = op_group.groupby('Numéro de support')

            for sta in station_groups.groups.keys():

                station_group = station_groups.get_group(sta).sort_values('Azimut')

                azimuths = station_group['Azimut'].drop_duplicates().reset_index(drop=True)
                az_count = len(azimuths)

                station_group = station_group.to_dict('list')

                out = rej_file if station_group['Hauteur / sol'][0] < 0 else out_file

                delimiters = {'supp_num': [], 'lat': [], 'lng': [], 'del_lat': [], 'del_lng': []}

                az_assoc = {}

                last_az_max = 0
                az_min_zero = 0

                az_min, az_max = None, None

                for i in range(az_count):
                    curr_az = azimuths[i]

                    if az_count == 1:
                        az_min = curr_az - 60
                        az_max = curr_az + 60
                    elif az_count > 1 and i == az_count - 1:
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

                    az_assoc[curr_az] = (az_min, az_max)

                az_delimited = []

                for i in range(len(station_group['Numéro Cartoradio'])):

                    ant_az = station_group['Azimut'][i]

                    supp_num = station_group['Numéro de support'][i]

                    lat = station_group['Latitude'][i]
                    lng = station_group['Longitude'][i]

                    ant_az_min = az_assoc[ant_az][0]
                    ant_az_max = az_assoc[ant_az][1]

                    freq_unit = station_group['Unité'][i]
                    beg_freq = calculate_freq(station_group['Début'][i], freq_unit)
                    end_freq = calculate_freq(station_group['Fin'][i], freq_unit)

                    out.write_row([
                        'BS_ANTENNA', supp_num, station_group['Numéro Cartoradio'][i],
                        lat, lng, station_group['Hauteur / sol'][i], station_group['Adresse'][i],
                        station_group['Commune'][i], station_group["Numéro d'antenne"][i],
                        lat + 0.0005 * math.cos(ant_az * np.pi / 180),
                        lng + 0.0005 * math.sin(ant_az * np.pi / 180),
                        ant_az, ant_az_min, ant_az_max, beg_freq, end_freq
                    ])

                    if ant_az_min % 360 not in az_delimited:
                        az_delimited.append(ant_az_min % 360)
                        del_coords = calculate_delimiters(lat, lng, ant_az_min)
                        insert_data(
                            delimiters,
                            {
                                'supp_num': [supp_num],
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
                                'supp_num': [supp_num],
                                'lat': [lat],
                                'lng': [lng],
                                'del_lat': [del_coords[0]],
                                'del_lng': [del_coords[1]]
                            },
                            1
                        )

                for i in range(len(delimiters['supp_num'])):
                    out.write_row(
                        ['DELIMITER', delimiters['supp_num'][i], delimiters['lat'][i],
                         delimiters['lng'][i], delimiters['del_lat'][i], delimiters['del_lng'][i]]
                    )


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
