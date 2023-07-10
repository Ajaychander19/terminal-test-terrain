"""This module defines CellAssociator class and methods to associate base stations / antennas to each measurement."""
import math
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
        'MEAS_NB': ['NA', 'NA', 'NA', 'NA', 'nb_meas_for_1', 'nb_meas_for_2', 'nb_meas_for_3', 'etc'],
        'MEASUREMENT': ['Timestamp', 'Lat', 'Lng', 'Measurement_Name', 'Values'],
        'DELIMITER': ['Cartoradio_Number', 'Support_Lat', 'Support_Lng', 'Del_Lat', 'Del_Lng'],
        'BS_ANT_DIR': ['Cartoradio_Number', 'Ant_Number', 'Support_Lat', 'Support_Lng', 'Dest_Lng', 'Dest_Lat'],
        'ASSOC': ['Cartoradio_Number', 'Ant_Number', 'TAC', 'CID', 'EARFCN', 'PCI'],
        'POINT': ['Lat', 'Lng', 'TAC', 'CID', 'EARFCN', 'PCI', 'RSRP', 'RSRQ', 'RSSI', 'CINR']
    }

    # Association file header V2
    _HEADER_V2 = {
        'MEAS_EARFCNS': ['NA', 'NA', 'NA', 'NA', 'EARFCN1', 'EARFCN2', 'EARFCN3', 'etc'],
        'MEAS_PCIS': ['NA', 'NA', 'NA', 'NA', 'PCI1', 'PCI2', 'PCI3', 'etc'],
        'MEAS_BEAMS': ['NA', 'NA', 'NA', 'NA', 'BEAM1', 'BEAM2', 'BEAM3', 'etc'],
        'MEAS_NB': ['NA', 'NA', 'NA', 'NA', 'nb_meas_for_1', 'nb_meas_for_2', 'nb_meas_for_3', 'etc'],
        'MEASUREMENT': ['Timestamp', 'Lat', 'Lng', 'Measurement_Name', 'Values'],
        'DELIMITER': ['Cartoradio_Number', 'Support_Lat', 'Support_Lng', 'Del_Lat', 'Del_Lng'],
        'BS_ANT_DIR': ['Cartoradio_Number', 'Ant_Number', 'Support_Lat', 'Support_Lng', 'Dest_Lng', 'Dest_Lat'],
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
        self._in_meas = in_meas     # Measurements file path ad name.
        self._outdir = outdir       # Output file directory.
        self._point_assoc = None    # Association between points and measurements.
        self._antennas = None       # Antennas
        self.version = None         # None => 4G ,v2 => 5G

    def calculate_association(self):
        """Calculates the association between EARFCNs / PCIs and base stations."""

        print('Calculating association...')
        file_name = os.path.join(self._outdir, 'assoc_{0}_{1}.csv'.format(
                    pathlib.Path(self._in_meas).stem.replace("cev",""),
                    pathlib.Path(self._in_sites).stem.replace("cev","")))
        header = self._HEADER
        if self.version == "2.0":
            header = self._HEADER_V2
        with csvt.CSVWriter(file_name, header) as out_wr:

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
                elif line[0] == 'VERSION' and line[1] == "2.0":
                    self.version = 2.0
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
                    if self.version == "2.0":
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

                    #if len(earpcis) + 5 != len(line):
                    #    raise RuntimeError('error: the measurement does not contains as much values than EARFCNs/PCIs.')

                    #if last_earfcn is None or last_pci is None:
                    #    raise RuntimeError('error: MEASUREMENT encountered before MEASURE_SERVING.')
                    #out_wr.write_row(line)

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

    def _associate_data(self, MIN_NUMBER_OF_MEASURES_FOR_ASSOCIATION=50):
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
                #admission_score = totalweight/card
                #nb_of_large = (weights> 0.5).sum()

                if (totalweight>10):

                    # For each Voronoi cell...
                    for vor_key in vor_groups.groups.keys():  # i

                        vgroup = vor_groups.get_group(vor_key)  # Group of antennas in the Voronoi cell.
                        vlen = len(vgroup)  # Number of antennas in the Voronoi cell.
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
                        # minus artan2 should be considered since the angles are CLOCKWISE for azimut
                        angles = np.arctan2(dirs_east, dirs_north)
                        distPoints = np.sqrt(dirs_east ** 2 + dirs_north ** 2)

                        # calcul d'un score prendant la distance
                        # principe : si la distance augmente, le signal diminue. On essaye de trouver un produit
                        # qui soit cosntant idéalement constant et on regarde l'inverse de l'indice de Jain
                        # valeur 1 : excellent
                        # valeur>1 : assez mauvais

                        #fact1 = (dirs_east**2+dirs_north**2)**1.5 * np.exp(points_rsrps*np.log(10)/10)
                        #fact1 =  np.sqrt(dirs_east ** 2 + dirs_north ** 2) * weights**2
                        #fact2 = fact1 ** 2
                        #distbis = card * np.sum(fact2) / np.sum(fact1)**2
                        #distbis = np.mean((dirs_east**2+dirs_north**2)**1.5 * np.exp(points_rsrps*np.log(10)/10)) # version 2 : on singe loi de propagation
                        #distbis = np.mean((dirs_east ** 2 + dirs_north ** 2) * weights**2)  # version 1 :

                        # correlation entre distance et poids, si tres proche de -1, distancebis est null, c'est bon
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
                                    theta_argmax[3][3], ')  score=',theta_max)

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
                                          theta_list[argmin_dist][3][3],')  score=',theta_max, 'Rem : closest')
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
                                          theta_argmax[3][3],')  score=',theta_max)



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
                                NoteMax = self._assocsProp['Score'][i] + self._assocsProp['Score'][j]  # on force note de chacune a somme des notes
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
                        'Score': [self._assocsProp['Score'][i]]
                    }, 1)
        print(self._assocs)

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
                self._assocs['CID'][i], self._assocs['EARFCN'][i], self._assocs['PCI'][i], self._assocs['Score'][i]
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
