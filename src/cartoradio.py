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
        'Latitude', 'Longitude', 'Hauteur en m', 'Adresse', 'Commune'
    ]]

    # Removing useless entries, keeping only directive LTE antennas.
    siteant = siteant[is_system_valid(siteant['Système']) & (siteant['Directivité'] == 'Directif')]

    # Grouping by operators.
    op_groups = siteant.groupby('Exploitant')

    # Output CSV file header
    header = {
        'ANTENNA': [
            'Support_Number', 'Cartoradio_Number', 'Lat', 'Lng', 'Height', 'Info_Addr', 'Info_Municipality',
            'Ant_Number', 'Dest_Lat', 'Dest_Lng', 'Azimuth', 'AzimuthMin', 'AzimuthMax'
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
                station_group = station_groups.get_group(sta).sort_values('Azimut').to_dict('list')
                slen = len(station_group['Exploitant'])

                out = rej_file if station_group['Hauteur en m'][0] < 0 else out_file

                # Inserting ANTENNA entry.
                azimuths = station_group['Azimut']

                delimiters = {'supp_num': [], 'lat': [], 'lng': [], 'azimuth': []}

                last_az_max = 0
                az_min_zero = 0

                for i in range(slen):

                    if not station_group['Hauteur en m'][0] < 0:

                        # Calculating min azimuth and max azimuth.
                        azimuth = azimuths[i]
                        az_min, az_max = None, None

                        if slen == 1:
                            az_min = azimuth - 60
                            az_max = azimuth + 60
                        elif slen > 1 and i == slen - 1:
                            az_min = last_az_max
                            az_max = az_min_zero + 360
                        elif slen > 1 and i == 0:
                            az_min = min((azimuth + azimuths[slen - 1] - 360) / 2, (azimuth + azimuths[i + 1]) / 2)
                            az_max = min((azimuth + azimuths[slen - 1] - 360) / 2, (azimuth + azimuths[i + 1]) / 2)
                            az_min_zero = az_min
                        elif slen > 1 and i > 0:
                            az_min = min((azimuth + azimuths[i - 1]) / 2, (azimuth + azimuths[i + 1]) / 2)
                            az_max = max((azimuth + azimuths[i - 1]) / 2, (azimuth + azimuths[i + 1]) / 2)

                        supp_num = station_group['Numéro de support'][i]

                        last_az_max = az_max

                        lat, lng = station_group['Latitude'][i], station_group['Longitude'][i]

                        if not (az_min is None or az_max is None):
                            if az_min % 360 not in delimiters['azimuth'] and az_min >= 0 and az_min % 360 != azimuth:
                                insert_data(
                                    delimiters,
                                    {
                                        'supp_num': [supp_num], 'lat': [lat], 'lng': [lng],
                                        'azimuth': [az_min]
                                    },
                                    1
                                )
                            if az_max % 360 not in delimiters['azimuth'] and az_max >= 0 and az_max % 360 != azimuth:
                                insert_data(
                                    delimiters,
                                    {
                                        'supp_num': [supp_num], 'lat': [lat], 'lng': [lng],
                                        'azimuth': [az_max]
                                    },
                                    1
                                )

                    out.write_row([
                        'ANTENNA', supp_num, station_group['Numéro Cartoradio'][i],
                        lat, lng, station_group['Hauteur en m'][i], station_group['Adresse'][i], station_group['Commune'][i],
                        station_group["Numéro d'antenne"][i],
                        lat + 0.0005 * math.cos(azimuth * np.pi / 180),
                        lng + 0.0005 * math.sin(azimuth * np.pi / 180),
                        station_group['Azimut'][i], az_min, az_max    # TODO Calculate pointDest and pointZone
                    ])

                dels = [
                    calculate_delimiters(
                        delimiters['lat'][i], delimiters['lng'][i], delimiters['azimuth'][i]
                    ) for i in range(len(delimiters['azimuth']))
                ]

                for i in range(len(dels)):
                    out.write_row(
                        ['DELIMITER', delimiters['supp_num'][i], delimiters['lat'][i],
                         delimiters['lng'][i], dels[i][0], dels[i][1]]
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
