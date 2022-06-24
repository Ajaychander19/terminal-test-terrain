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
    siteant = siteant[
        'Numéro de support', 'Numéro Cartoradio', 'Numéro de Station',
        'Exploitant', "Numéro d'antenne", 'Directivité', 'Azimut', 'Système',
        'Latitude', 'Longitude', 'Hauteur', 'Adresse', 'Commune'
    ]

    # Removing useless entries, keeping only directive LTE antennas.
    siteant = siteant[is_system_valid(siteant['Système']) & siteant['Directivité']]

    # Grouping by operators.
    op_groups = siteant.groupby('Exploitant')

    # Output CSV file header
    header = {
        'ANTENNA': [
            'Support_Number', 'Cartoradio_Number', 'Lat', 'Lng', 'Height', 'Info_Addr', 'Info_Municipality',
            'Ant_Number', 'Dest_Lat', 'Dest_Lng', 'Zone_Lat', 'Zone_Lng', 'Azimuth', 'AzimuthMin', 'AzimuthMax'
        ]
    }

    # Reading

    for op in op_groups.groups.keys():

        with csvtools.CSVWriter('{0}/sites_{1}.csv'.format(output_dir, op), header) as out_file, \
                csvtools.CSVWriter('{0}/rejected_{1}.csv'.format(output_dir, op), header) as rej_file:

            op_group = op_groups.get_group(op)
            station_groups = op_groups.groupby['Numéro de support']

            for sta in station_groups.groups.keys():

                station_group = station_groups.get_group(sta).sort_values('Azimuth').to_dict('list')
                slen = len(station_group['Exploitant'])

                out = rej_file if station_group['Hauteur'] < 0 else out_file

                # Inserting ANTENNA entry.
                azimuths = station_group['Azimuth']
                last_az_max = 0
                az_min_zero = 0

                for i in range(slen):

                    # Calculating min azimuth and max azimuth.
                    azimuth = azimuths[i]
                    az_min, az_max = 0, 0

                    if slen == 1:
                        az_min = azimuth - 60
                        az_max = azimuth + 60
                    elif slen > 1 and i == slen - 1:
                        az_min = last_az_max
                        az_max = az_min_zero + 360
                    elif slen > 1 and i == 0:
                        az_min = min((azimuth + azimuths[slen - 1] - 360) / 2, (azimuth + azimuths[i + 1]) / 2)
                        az_max = max((azimuth + azimuths[slen - 1] - 360) / 2, (azimuth + azimuths[i + 1]) / 2)
                        az_min_zero = 0
                    elif slen > 1 and i > 0:
                        az_min = min((azimuth + azimuths[i - 1]) / 2, (azimuth + azimuths[i + 1]) / 2)
                        az_max = max((azimuth + azimuths[i - 1]) / 2, (azimuth + azimuths[i + 1]) / 2)

                    last_az_max = az_max

                    lat, lng = station_group['Latitude'][i], station_group['Longitude'][i]

                    out.write_row([
                        'ANTENNA', station_group['Numéro de support'][i], station_group['Numéro Cartoradio'][i],
                        lat, lng, station_group['Hauteur'][i], station_group['Adresse'][i], station_group['Commune'][i],
                        station_group["Numéro d'antenne"][i],
                        lat + (0.5 * math.pow(10, -3)) * math.cos(azimuth * math.pi / 180),
                        lng + (0.5 * math.pow(10, -3)) * math.sin(azimuth * math.pi / 180),

                        0.0, station_group['Azimuth'][i], az_min, az_max    # TODO Calculate pointDest and pointZone
                    ])

    # Base station list
    stations = []


def is_system_valid(ser: pd.Series) -> pd.Series:
    res = []
    for s in ser:
        res.append('LTE' in s)  # or '5G' in s
    return pd.Series(res)
