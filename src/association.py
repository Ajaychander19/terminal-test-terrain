import pandas as pd
import numpy as np
import csvtools as csvt
import shapely.geometry as geom
import scipy.spatial as sp

# FIXME Temporary
import matplotlib.pyplot as plt

from dictutils import insert_data


class CellAssociator:

    _HEADER = {
        'MEAS_EARFCNS': ['NA', 'NA', 'NA', 'NA', 'EARFCN1', 'EARFCN2', 'EARFCN3', 'etc'],
        'MEAS_PCIS': ['NA', 'NA', 'NA', 'NA', 'PCI1', 'PCI2', 'PCI3', 'etc'],
        'MEASUREMENT': ['Timestamp', 'Lat', 'Lng', 'Measurement_Name', 'Values'],
        'DELIMITER': ['Support_Number', 'Support_Lat', 'Del_Lat', 'Del_Lng']
    }

    def __init__(self, in_meas: str, in_sites: str, outdir: str):
        self._in_sites = in_sites
        self._in_meas = in_meas
        self._outdir = outdir
        self._antennas_dict = {
            'Cartoradio_Number': [], 'Ant_Number': [], 'Lat': [], 'Lng': [], 'Dest_Lat': [], 'Dest_Lng': [],
            'Azimuth': [], 'AzimuthMin': [], 'AzimuthMax': []
        }
        self._serving_dict = {'Timestamp': [], 'Lat': [], 'Lng': [], 'EARFCN': [], 'PCI': []}
        self._cellinfo_dict = {'EARFCN': [], 'PCI': [], 'TAC': [], 'CID': []}
        self._rsrps = {'Timestamp': [], 'RSRP': []}
        self._measurements = {'Timestamp': [], 'RSRP': []}
        self._earpcis = []
        self._point_assoc = None
        self._epassoc = {}

    def process_data(self):
        pass

    def _initial_read(self, out_wr: csvt.CSVWriter):

        # Last recorded EARFCN / PCI.
        last_earfcn = None
        last_pci = None

        # Reading measurement file.
        with csvt.CSVReader(self._in_meas) as meas:

            line = meas.read_line()

            while line != ['']:

                # Registering base stations.
                if line[0] == 'CELLINFO':

                    if len(line) < 10:
                        raise RuntimeError('error: CELLINFO line must contain at least 10 fields')

                    insert_data(
                        self._cellinfo_dict,
                        {'EARFCN': [int(line[4])], 'PCI': [int(line[5])], 'TAC': [int(line[6])], 'CID': [int(line[7])]},
                        1
                    )

                # Registering measurements...
                elif line[0] == 'MEASURE_SERVING':

                    if len(line) < 6:
                        raise RuntimeError('error: MEASURE_SERVING line must contain at least 6 fields')

                    insert_data(
                        self._serving_dict,
                        {'Timestamp': [float(line[1])], 'Lat': [float(line[2])],
                         'Lng': [float(line[3])], 'EARFCN': [int(line[4])], 'PCI': [int(line[5])]},
                        1
                    )

                    last_earfcn = int(line[4])
                    last_pci = int(line[5])

                # Registering EARFCN / PCI...
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

                    self._earpcis = [(int(i), int(j)) for (i, j) in zip(line[5:], lineb[5:])]

                    out_wr.write_row(line)
                    out_wr.write_row(lineb)

                # Registering measurement data...
                elif line[0] == 'MEASUREMENT':

                    if not self._earpcis:
                        raise RuntimeError('error: EARFCNS/PCIS not declared.')

                    if len(self._earpcis) + 5 != len(line):
                        raise RuntimeError('error: the measurement does not contains as much values than EARFCNs/PCIs.')

                    if last_earfcn is None or last_pci is None:
                        raise RuntimeError('error: MEASUREMENT encountered before MEASURE_SERVING.')

                    if line[4] == 'RSRP':
                        rsrp_index = self._earpcis.index((last_earfcn, last_pci)) + 5
                        insert_data(
                            self._rsrps,
                            {
                                'Timestamp': [float(line[1])],
                                'RSRP': [float(line[rsrp_index]) if line[rsrp_index] != '' else None]
                            },
                            1
                        )

                    out_wr.write_row(line)

                elif line[0] == 'MEAS_PCIS':
                    raise RuntimeError('error: MEAS_PCIS line must be directly preceded by a MEAS_EARFCNS line.')

                line = meas.read_line()

            # Associating measurement points to corresponding base stations...
            self._point_assoc = pd.merge(
                pd.DataFrame(self._cellinfo_dict), pd.DataFrame(self._serving_dict),
                on=['EARFCN', 'PCI']
            )

            # Associating points to corresponding RSRPs...
            self._point_assoc = pd.merge(
                self._point_assoc, pd.DataFrame(self._rsrps),
                on=['Timestamp']
            ).drop_duplicates(subset=['Timestamp']).sort_values(['Timestamp'])

            pass

    def _read_antennas(self, out_wr: csvt.CSVWriter):

        # {
        #     'Cartoradio_Number': [], 'Ant_Number': [], 'Lat': [], 'Lng': [], 'Dest_Lat': [], 'Dest_Lng': [],
        #     'Azimuth': [], 'AzimuthMin': [], 'AzimuthMax': []
        # }

        with csvt.CSVReader(self._in_sites) as sites:

            line = sites.read_line()

            while line != ['']:

                if line[0] == 'BS_ANTENNA':

                    insert_data(
                        self._antennas_dict,
                        {
                            'Cartoradio_Number': [int(line[2])], 'Ant_Number': [int(line[8])],
                            'Lat': [float(line[3])], 'Lng': [float(line[4])], 'Dest_Lat': [float(line[9])],
                            'Dest_Lng': [float(line[10])], 'Azimuth': [float(line[11])],
                            'AzimuthMin': [float(line[12])],  'AzimuthMax': [float(line[13])]
                        },
                        1
                    )

                elif line[0] == 'DELIMITER':
                    out_wr.write_row(line)

                line = sites.read_line()

            self._antennas = pd.DataFrame(self._antennas_dict)

    def _process_geometry(self):

        assocs = {}

        # Calculating Voronoi cells.

        bs_coords = np.array(list(self._antennas.groupby(['Lat', 'Lng']).groups.keys()))

        vor = sp.Voronoi(bs_coords)

        bs_vor = {'Lat': [], 'Lng': [], 'Vor': []}

        for i in range(len(vor.points)):
            point = vor.points[i]
            p_reg = vor.point_region[i]
            region = vor.regions[p_reg]
            if -1 not in region and region:
                insert_data(bs_vor, {
                    'Lat': [point[0]],
                    'Lng': [point[1]],
                    'Vor': [p_reg]
                }, 1)

        # bs_vor = {
        #     'Lat': [x for (x, y) in vor.points],
        #     'Lng': [y for (x, y) in vor.points],
        #     'Vor': vor.point_region
        # }

        ant_vor_sectors = pd.merge(self._antennas, pd.DataFrame(bs_vor), on=['Lat', 'Lng']).drop_duplicates(
            ['Cartoradio_Number', 'Ant_Number'])

        # PLOT
        sp.voronoi_plot_2d(vor)

        #ats_dict = ant_vor_sectors.to_dict('list')

        # Calculating convex hulls.
        point_groups = self._point_assoc.groupby(['TAC', 'CID', 'EARFCN', 'PCI'])

        groups = {}
        hulls = {}

        gr_keys = point_groups.groups.keys()

        for gr_key in gr_keys:
            gr = point_groups.get_group(gr_key)
            coords = np.array(list(zip(gr['Lat'], gr['Lng'])))
            groups[gr_key] = coords
            hulls[gr_key] = geom.MultiPoint(coords).convex_hull

        v_weight = np.vectorize(weight)
        v_sigma = np.vectorize(calc_sigma)
        v_psi = np.vectorize(lambda x: 1.0 if x else 0.0)
        v_theta = np.vectorize(calc_theta)
        v_belongs = np.vectorize(belongs)
        v_valid = np.vectorize(is_valid)


        vor_groups = ant_vor_sectors.groupby(['Vor'])

        for gr_key in gr_keys:      # n

            # Indicators
            theta_values = {}

            point_group = point_groups.get_group(gr_key)

            points_lat = point_group['Lat'].to_numpy()
            points_lng = point_group['Lng'].to_numpy()
            points_rsrps = point_group['RSRP'].to_numpy()
            card = len(point_group)

            angles = np.arctan2(points_lat, points_lng)
            weights = v_weight(points_rsrps)

            for vor_key in vor_groups.groups.keys(): # i

                vgroup = vor_groups.get_group(vor_key)
                vlen = len(vgroup)
                vgroup = vgroup.to_dict('list')
                vor_shape = geom.Polygon(vor.vertices[vor.regions[vor_key]])

                if vor_shape.intersects(hulls[gr_key]):

                    # PLOT
                    x, y = vor_shape.exterior.xy
                    plt.plot(x, y)
                    x, y = hulls[gr_key].exterior.xy if type(hulls[gr_key]) != geom.LineString else hulls[gr_key].xy
                    plt.plot(x, y)
                    x, y = [k[0] for k in groups[gr_key]], [k[1] for k in groups[gr_key]]
                    plt.scatter(x, y, s=0.25)


                    points_belongs = v_belongs(points_lat, points_lng, vor_shape)

                    for i in range(vlen):   # j

                        az_min = vgroup['AzimuthMin'][i]
                        az_max = vgroup['AzimuthMax'][i]

                        sigma_sum = v_sigma(angles, weights, az_min, az_max)
                        sigma = np.sum(sigma_sum) / card
                        psi_sum = v_psi(points_belongs) * sigma_sum
                        psi = np.sum(psi_sum) / card
                        theta = calc_theta(sigma, psi)
                        if not theta == 0.0:
                            theta_values[
                                (vgroup['Cartoradio_Number'][i], vgroup['Ant_Number'][i], gr_key)
                            ] = (sigma, psi, theta)

            if theta_values:
                print(theta_values)
                # theta_argmax = max(theta_values, key=lambda k: theta_values[k])
                # theta_max = theta_values[theta_argmax]
                # theta_argmax = [k for k in theta_values.keys()]
                # theta_array = np.array([theta_values[k] for k in theta_values.keys()])
                #
                # if theta_array.size > 0:
                #     valids = v_valid(theta_max, theta_array, 0.08)
                #     if valids.size > 0:
                #         if np.all(valids):
                #             print(theta_argmax)
        #PLOT
        plt.show()

    def write_outfile(self):
        pass


def weight(rsrp: float) -> float:
    if rsrp <= -100:
        return 0.15
    elif -100 < rsrp < -80:
        return 0.6
    else:
        return 1.0


def calc_sigma(a: float, w: float, az_min: float, az_max: float):
    return w * (1.0 if az_min < a < az_max else 0.0)


def calc_theta(sigma: float, psi: float) -> float:
    return 0.0 if psi < 0.25 else (0.8 * sigma + 0.2 * psi)


def belongs(x: float, y: float, shape: geom.Polygon) -> bool:
    return shape.contains(geom.Point(x, y))


def is_valid(theta_max: float, other_theta: float, const: float):
    if theta_max == 0.0 or other_theta / theta_max == 0.0:
        return True
    else:
        return np.abs(np.log10(other_theta / theta_max)) > const
