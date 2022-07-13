"""This module defines CellAssociator class and methods to associate base stations / antennas to each measurement."""

import os.path
import pathlib

import pandas as pd
import numpy as np
import csvtools as csvt
import shapely.geometry as geom
import scipy.spatial as sp

from dictutils import insert_data, fill_data


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
        'MEASUREMENT': ['Timestamp', 'Lat', 'Lng', 'Measurement_Name', 'Values'],
        'DELIMITER': ['Support_Number', 'Support_Lat', 'Del_Lat', 'Del_Lng'],
        'BS_ANT_DIR': ['Cartoradio_Number', 'Ant_Number', 'Dest_Lng', 'Dest_Lat'],
        'ASSOC': ['Cartoradio_Number', 'Ant_Number', 'TAC', 'CID', 'EARFCN', 'PCI'],
        'POINT': ['Lat', 'Lng', 'TAC', 'CID', 'EARFCN', 'PCI', 'RSRP', 'RSRQ', 'RSSI', 'CINR']
    }

    def __init__(self, in_meas: str, in_sites: str, outdir: str):
        """Class constructor.

        Parameters:
            in_meas: path of the input measurement file.
            in_sites: path of the input "sites" file.
            outdir: path of the output file.
        """

        self._in_sites = in_sites   # Sites file path.
        self._in_meas = in_meas     # Measurements file path.
        self._outdir = outdir       # Output file directory.
        self._point_assoc = None    # Association between points and measurements.
        self._antennas = None       # Antennas

    def calculate_association(self):
        """Calculates the association between EARFCNs / PCIs and base stations."""

        print('Calculating association...')

        with csvt.CSVWriter(
                os.path.join(self._outdir, 'assoc_{0}_{1}.csv'.format(
                    pathlib.Path(self._in_meas).stem, pathlib.Path(self._in_sites).stem)), self._HEADER) as out_wr:

            print('Reading measurements...')
            self._read_measurements(out_wr)

            print('Reading sites...')
            self._read_antennas(out_wr)

            print('Associating...')
            self._associate_data()

            print('Writing output...')
            self._write_output(out_wr)

    def _read_measurements(self, out_wr: csvt.CSVWriter):
        """PRIVATE METHOD which reads measurement file.

        Reads the measurement file and store data in memory.
        MEAS_EARFCNS, MEAS_PCIS and MEASUREMENT fields are reproduced in the output file.

        Parameters:
            out_wr: output file to be written.

        Raises:
            RuntimeError: if a problem occurs while decoding data from the file.

        """

        # Last recorded EARFCN / PCI (used to associate measurements to points).
        last_earfcn = None
        last_pci = None

        # Serving cell infos.
        serving_dict = {
            'Timestamp': [], 'Lat': [], 'Lng': [], 'EARFCN': [], 'PCI': [],
            'RSRP': [], 'RSRQ': [], 'RSSI': [], 'CINR': []
        }

        # Measurement infos.
        measurements = {'Timestamp': [], 'RSRP': [], 'RSRQ': [], 'RSSI': []}

        # Found cells information (SIB1).
        cellinfo_dict = {'EARFCN': [], 'PCI': [], 'TAC': [], 'CID': []}

        # EARFCNs / PCIs
        earpcis = []

        # Reading measurement file...
        with csvt.CSVReader(self._in_meas) as meas:

            line = meas.read_line()     # Current line.
            prev_tstamp = None          # Previous measurement timestamp.
            meas_count = 0              # Measurement count.

            while line != ['']:

                # Registering base stations.
                if line[0] == 'CELLINFO':

                    if len(line) < 10:
                        raise RuntimeError('error: CELLINFO line must contain at least 10 fields')

                    insert_data(
                        cellinfo_dict,
                        {'EARFCN': [int(line[4])], 'PCI': [int(line[5])], 'TAC': [int(line[6])], 'CID': [int(line[7])]},
                        1
                    )

                # Registering measurements...
                elif line[0] == 'MEASURE_SERVING':

                    if len(line) < 6:
                        raise RuntimeError('error: MEASURE_SERVING line must contain at least 6 fields')

                    insert_data(
                        serving_dict,
                        {'Timestamp': [float(line[1])], 'Lat': [float(line[2])],
                         'Lng': [float(line[3])], 'EARFCN': [int(line[4])], 'PCI': [int(line[5])],
                         'RSRP': [float(line[6])], 'RSRQ': [float(line[7])], 'RSSI': [float(line[8])],
                         'CINR': [float(line[9])]},
                        1
                    )

                    last_earfcn = int(line[4])
                    last_pci = int(line[5])

                # Registering EARFCN / PCI couples...
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

                    earpcis = [(int(i), int(j)) for (i, j) in zip(line[5:], lineb[5:])]

                    # Writing couples in file...
                    out_wr.write_row(line)
                    out_wr.write_row(lineb)

                # Registering measurement data...
                elif line[0] == 'MEASUREMENT':

                    if not earpcis:
                        raise RuntimeError('error: EARFCNS/PCIS not declared.')

                    if len(earpcis) + 5 != len(line):
                        raise RuntimeError('error: the measurement does not contains as much values than EARFCNs/PCIs.')

                    if last_earfcn is None or last_pci is None:
                        raise RuntimeError('error: MEASUREMENT encountered before MEASURE_SERVING.')

                    # # Associating measurements to points...
                    # meas_name = line[4]
                    #
                    # if meas_name == 'RSRP' or meas_name == 'RSRQ' or meas_name == 'RSSI':
                    #
                    #     # Corresponding index of the measurement following current EARFCN / PCI
                    #     meas_index = earpcis.index((last_earfcn, last_pci)) + 5
                    #
                    #     # Measurement value.
                    #     val = float(line[meas_index]) if line[meas_index] != '' else None
                    #
                    #     # Current measurement timestamp.
                    #     tstamp = float(line[1])
                    #
                    #     # Choosing where to insert data...
                    #     to_insert = {
                    #         'Timestamp': [float(line[1])],
                    #         'RSRP': [val] if meas_name == 'RSRP' else [None],
                    #         'RSRQ': [val] if meas_name == 'RSRQ' else [None],
                    #         'RSSI': [val] if meas_name == 'RSSI' else [None],
                    #     }
                    #
                    #     # Timestamp change -> point change...
                    #     if tstamp != prev_tstamp:
                    #
                    #         insert_data(measurements, to_insert, 1)
                    #         prev_tstamp = tstamp
                    #         meas_count += 1
                    #
                    #     else:   # otherwise merging previous measurement and new measurement.
                    #
                    #         fill_data(measurements, to_insert, meas_count - 1, 1)

                    # Copying measurement line into the output file (=/= point association !!!)
                    out_wr.write_row(line)

                elif line[0] == 'MEAS_PCIS':
                    raise RuntimeError('error: MEAS_PCIS line must be directly preceded by a MEAS_EARFCNS line.')

                line = meas.read_line()

            # Associating measurement points to corresponding base stations...
            self._point_assoc = pd.merge(
                pd.DataFrame(cellinfo_dict), pd.DataFrame(serving_dict),
                on=['EARFCN', 'PCI']
            ).drop_duplicates(subset=['Timestamp']).sort_values(['Timestamp'])

            # # Associating points to corresponding measurements...
            # self._point_assoc = pd.merge(
            #     self._point_assoc, pd.DataFrame(measurements),
            #     on=['Timestamp']
            # ).drop_duplicates(subset=['Timestamp']).sort_values(['Timestamp'])

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
            'Azimuth': [], 'AzimuthMin': [], 'AzimuthMax': []
        }

        # Reading antenna file...
        with csvt.CSVReader(self._in_sites) as sites:

            line = sites.read_line()

            while line != ['']:

                # Antenna info...
                if line[0] == 'BS_ANTENNA':

                    insert_data(
                        antennas_dict,
                        {
                            'Cartoradio_Number': [int(line[2])], 'Ant_Number': [int(line[8])],
                            'Lat': [float(line[3])], 'Lng': [float(line[4])], 'Dest_Lat': [float(line[9])],
                            'Dest_Lng': [float(line[10])], 'Azimuth': [float(line[11])],
                            'AzimuthMin': [float(line[12])],  'AzimuthMax': [float(line[13])]
                        },
                        1
                    )

                # Sector delimiter...
                elif line[0] == 'DELIMITER':
                    out_wr.write_row(line)

                line = sites.read_line()

            # Creating antennas information dataframe.
            self._antennas = pd.DataFrame(antennas_dict)

    def _associate_data(self):
        """PRIVATE METHOD which calculate the association between group of measurement points with
        sames EARFCNS/PCIS and base stations."""

        # Associations between antennas and EARFCNs / PCIs
        self._assocs = {'Cartoradio_Number': [], 'Ant_Number': [], 'TAC': [], 'CID': [], 'EARFCN': [], 'PCI': []}

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
        point_groups = self._point_assoc.groupby(
            ['TAC', 'CID', 'EARFCN', 'PCI'])

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
        for gr_key in gr_keys:      # n

            # "Theta" criteria values.
            theta_values = {}

            # Group of points and their RSRPs.
            point_group = point_groups.get_group(gr_key)
            points_rsrps = point_group['RSRP'].to_numpy()

            # Size of group.
            card = len(point_group)

            # Calculating weights...
            weights = v_weight(points_rsrps)

            # For each Voronoi cell...
            for vor_key in vor_groups.groups.keys():    # i

                vgroup = vor_groups.get_group(vor_key)      # Group of antennas in the Voronoi cell.
                vlen = len(vgroup)                          # Number of antennas in the Voronoi cell.
                vgroup = vgroup.to_dict('list')

                # Polygon of the Voronoi cell.
                vor_shape = geom.Polygon(vor.vertices[vor.regions[vor_key]])

                # Station / polygon distance calculation...

                linear_vor = geom.LinearRing(vor_shape.exterior.coords)

                # BS coords...
                vlat = vgroup['Lat'][0]
                vlng = vgroup['Lng'][0]

                # Projects the base station point over the current group of points convex hull...
                interp = linear_vor.interpolate(
                    linear_vor.project(geom.Point(vlat, vlng)))
                dist = np.sqrt(((vlat - interp.x) ** 2 + (interp.y - vlng) ** 2))

                # Calculating angles between points of base station and north over flat earth projection.

                # Points latitude / longitude...
                points_lat = point_group['Lat'].to_numpy()
                points_lng = point_group['Lng'].to_numpy()

                # Points coordinates over flat earth projection.
                dirs_north = (points_lat - vlat) * (np.pi / 180)
                dirs_east = (points_lng - vlng) * (np.pi / 180) * np.cos(vlat / 180 * np.pi)

                # Angles between north direction and point direction from the current base station.
                angles = np.arctan2(dirs_east, dirs_north)

                # Calculate values only if Voronoi cell intersects with the convex hull
                # of the current group of points.
                if vor_shape.intersects(hulls[gr_key]):

                    # Is each point belonging to the cell ?
                    points_belongs = v_belongs(points_lat, points_lng, vor_shape)

                    for i in range(vlen):   # j

                        # Azimuth delimitation of the sector.
                        az_min = vgroup['AzimuthMin'][i]
                        az_max = vgroup['AzimuthMax'][i]

                        # Criteria calculation.

                        # Angular criteria "sigma".
                        sigma_sum = v_sigma(angles, weights, az_min, az_max)
                        sigma = np.sum(sigma_sum) / card

                        # Cell belonging criteria "phi".
                        psi_sum = v_psi(points_belongs) * sigma_sum
                        psi = np.sum(psi_sum) / card

                        # Theta criteria calculation.

                        theta = calc_theta(sigma, psi)
                        if not theta == 0.0:
                            theta_values[
                                (vgroup['Cartoradio_Number'][i], vgroup['Ant_Number'][i], dist, gr_key)
                            ] = (sigma, psi, theta)

            # If non-zero theta values have been calculated...
            if theta_values:

                # Choosing one max theta value.
                theta_argmax = max(theta_values, key=lambda k: theta_values[k])
                theta_max = theta_values[theta_argmax]

                # Check for other max values, equals to the first max value.
                theta_argmax = [k for k in theta_values.keys()]

                # Other theta values.
                theta_array = np.array([theta_values[k] for k in theta_values.keys()])

                # Selecting antennas.
                if theta_array.size > 0:

                    # Select valid antennas following theta values.
                    valids = v_valid(theta_max, theta_array, 0.08)

                    # If valid antennas found, choose the antenna with a minimal distance
                    # with the convex hull of the current group of points.
                    if valids.size > 0:
                        if np.all(valids):
                            min_dist = theta_argmax[0][2]
                            argmin_dist = 0

                            # Selecting minimal base station / convex hull distance.
                            for i, selected in enumerate(theta_argmax):
                                dst = selected[2]
                                if dst < min_dist:
                                    min_dist = dst
                                    argmin_dist = i

                            # Inserting data.
                            insert_data(self._assocs, {
                                'Cartoradio_Number': [theta_argmax[argmin_dist][0]],
                                'Ant_Number': [theta_argmax[argmin_dist][1]],
                                'TAC': [theta_argmax[argmin_dist][3][0]], 'CID': [theta_argmax[argmin_dist][3][1]],
                                'EARFCN': [theta_argmax[argmin_dist][3][2]], 'PCI': [theta_argmax[argmin_dist][3][3]]
                            }, 1)

    def _write_output(self, out_wr: csvt.CSVWriter):
        """PRIVATE METHOD which writes relation calculated by _associate_datas in the output file.

        Produced fields are :
            - POINT: corresponds to a measurement point.
            - BS_ANT_DIR: describes the directivity of an antenna.
            - ASSOC: describe an association between an antenna and an EARFCN / PCI.

        Parameters:
            out_wr: output file.
        """

        # Writing antennas directivity.
        ants = self._antennas.groupby(['Ant_Number'])

        for a in ants.groups.keys():

            ant = ants.get_group(a).to_dict('list')

            out_wr.write_row([
                'BS_ANT_DIR', ant['Cartoradio_Number'][0], ant['Ant_Number'][0], ant['Lat'][0],
                ant['Lng'][0], ant['Dest_Lat'][0], ant['Dest_Lng'][0]
            ])

        # Writing associations
        for i in range(len(self._assocs['Cartoradio_Number'])):
            out_wr.write_row([
                'ASSOC', self._assocs['Cartoradio_Number'][i], self._assocs['Ant_Number'][i], self._assocs['TAC'][i],
                self._assocs['CID'][i], self._assocs['EARFCN'][i], self._assocs['PCI'][i]
            ])

        # Writing points.

        point_assoc = self._point_assoc.to_dict('list')
        for i in range(len(point_assoc['Lat'])):
            out_wr.write_row([
                'POINT', point_assoc['Lat'][i], point_assoc['Lng'][i], point_assoc['TAC'][i],
                point_assoc['CID'][i], point_assoc['EARFCN'][i], point_assoc['PCI'][i],
                point_assoc['RSRP'][i], point_assoc['RSRQ'][i], point_assoc['RSSI'][i],
                point_assoc['CINR'][i]
            ])

        print(pd.DataFrame(self._assocs))


def weight(rsrp: float) -> float:
    """Calculate the weight of a point using its RSRP.

    Parameters:
        rsrp: RSRP value of the point.

    Returns:
        Weight of the point, which is 0.15 if the RSRP is lesser than or equal to -100 dBm, 0.6 if the RSRP is between
        -100 dBm and -80 dBm, or 1.0 if the RSRP is greater than or equal to -80 dBm.
    """
    if rsrp <= -100:
        return 0.15
    elif -100 < rsrp < -80:
        return 0.6
    else:
        return 1.0


def calc_sigma(a: float, w: float, az_min: float, az_max: float):
    """Calculates the "sigma" angular indicator of one measurement point.

    Parameters:
        a: angle between the north direction and the point direction over flat earth projection.
        w: weight of the point.
        az_min: minimum azimuth of the sector.
        az_max: maximum azimuth of the sector.

    Returns:
        the weight of the point if a is between az_min and az_max, 0.0 otherwise.
    """
    return w if az_min < a < az_max else 0.0


def calc_theta(sigma: float, psi: float) -> float:
    """Calculate the "theta" indicator of a point from its sigma and psi values.

    Parameters:
        sigma: "sigma" angular indicator of the point.
        psi: "psi" cell belonging indicator of the point.

    Returns:
        theta, where theta = 0.8 * sigma + 0.2 * psi, if theta < 0.25, returns 0.0 otherwise.
    """
    return 0.0 if psi < 0.25 else (0.8 * sigma + 0.2 * psi)


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
    """Calculate the validity criteria for antenna selection for a given group of theta value.

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
        return np.abs(np.log10(other_theta / theta_max)) > threshold
