import pandas as pd
import numpy as np
import csvtools as csvt
import shapely.geometry as geom

from dictutils import insert_data


class CellAssociator:

    _HEADER = {
        'MEAS_EARFCNS': ['NA', 'NA', 'NA', 'NA', 'EARFCN1', 'EARFCN2', 'EARFCN3', 'etc'],
        'MEAS_PCIS': ['NA', 'NA', 'NA', 'NA', 'PCI1', 'PCI2', 'PCI3', 'etc'],
        'MEASUREMENT': ['Timestamp', 'Lat', 'Lng', 'Measurement_Name', 'Values']
    }

    def __init__(self, in_meas: str, in_sites: str, outdir: str):
        self._in_sites = in_sites
        self._in_meas = in_meas
        self._outdir = outdir
        self._serving_dict = {'Timestamp': [], 'Lat': [], 'Lng': [], 'EARFCN': [], 'PCI': []}
        self._cellinfo_dict = {'EARFCN': [], 'PCI': [], 'TAC': [], 'CID': []}
        self._rsrps = {'Timestamp': [], 'RSRP': []}
        self._measurements = {'Timestamp': [], 'RSRP': []}
        self._earpcis = []

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
                        {'EARFCN': [line[4]], 'PCI': [line[5]], 'TAC': [line[6]], 'CID': [line[7]]},
                        1
                    )

                # Registering measurements...
                elif line[0] == 'MEASURE_SERVING':

                    if len(line) < 6:
                        raise RuntimeError('error: MEASURE_SERVING line must contain at least 6 fields')

                    insert_data(
                        self._serving_dict,
                        {'Timestamp': [line[1]], 'Lat': [line[2]], 'Lng': [line[3]], 'EARFCN': [line[4]], 'PCI': [line[5]]},
                        1
                    )

                    last_earfcn = line[4]
                    last_pci = line[5]

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

                    self._earpcis = list(zip(line[5:], lineb[5:]))

                    out_wr.write_row(line)
                    out_wr.write_row(lineb)

                # Registering measurement datz...
                elif line[0] == 'MEASUREMENT':

                    if not self._earpcis:
                        raise RuntimeError('error: EARFCNS/PCIS not declared.')

                    if len(self._earpcis) + 5 != len(line):
                        raise RuntimeError('error: the measurement does not contains as much values than EARFCNs/PCIs.')

                    if last_earfcn is None or last_pci is None:
                        raise RuntimeError('error: MEASUREMENT encountered before MEASURE_SERVING.')

                    if line[4] == 'RSRP':
                        rsrp_index = self._earpcis.index((last_earfcn, last_pci)) + 5
                        insert_data(self._rsrps, {'Timestamp': [line[1]], 'RSRP': [line[rsrp_index]]}, 1)

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
            ).drop_duplicates(subset=['Timestamp'])

    def _produce_geometry(self, out_wr: csvt.CSVWriter):

        pass

        # tac_groups = self._point_assoc.groupby(['TAC'])
        #
        # for gr in tac_groups.groups.keys():
        #     tac_gr = tac_groups.get_group(gr)
        #
        #     earpci_groups = tac_gr.groupby(['EARFCN', 'PCI'])





    def write_outfile(self):
        pass


def weight(rsrp: float) -> float:
    if rsrp <= -100:
        return 0.15
    elif -100 < rsrp < -80:
        return 0.9
    else:
        return 1.0
