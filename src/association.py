import pandas as pd
import numpy as np
import csvtools as csvt
import shapely.geometry as geom

from dictutils import insert_data


class CellAssociator:

    def __init__(self, in_meas: str, in_sites: str, outdir: str):
        self._in_sites = in_sites
        self._in_meas = in_meas
        self._outdir = outdir
        self._serving_dict = {'Timestamp': [], 'Lat': [], 'Lng': [], 'EARFCN': [], 'PCI': []}
        self._cellinfo_dict = {'EARFCN': [], 'PCI': [], 'TAC': [], 'CID': []}
        self._measurements = {'Timestamp': [], 'RSRP': []}
        self._earpcis = []

    def read_meas(self):

        with csvt.CSVReader(self._in_meas) as meas:

            line = meas.read_line()

            if line[0] == 'CELLINFO':

                if len(line) < 10:
                    raise RuntimeError('error: CELLINFO line must contain at least 10 fields')

                insert_data(
                    self._cellinfo_dict,
                    {'EARFCN': [line[4]], 'PCI': [line[5]], 'TAC': [line[6]], 'CID': [line[7]]},
                    1
                )

            elif line[0] == 'MEASURE_SERVING':

                if len(line) < 6:
                    raise RuntimeError('error: MEASURE_SERVING line must contain at least 6 fields')

                insert_data(
                    self._serving_dict,
                    {'Timestamp': line[1], 'Lat': line[2], 'Lng': line[3], 'EARFCN': line[4], 'PCI': line[5]},
                    1
                )

            elif line[0] == 'MEAS_EARFCNS':

                if len(line) < 6:
                    raise RuntimeError('error: MEAS_EARFCNS line must contain at least 6 fields')

                lineb = meas.read_line()

                if lineb[0] != 'MEAS_PCIS':
                    raise RuntimeError('error: MEAS_EARFCNS line must be followed by MEAS_PCIS line.')

                if len(lineb) < 6:
                    raise RuntimeError('error: MEAS_PCIS line must contain at least 6 fields')

                if len(line) != len(lineb):
                    raise RuntimeError('error: MEAS_EARFCNS and MEAS_PCIS line shold have the same length.')

                self._earpcis = list(zip(line[5:], lineb[5:]))

            elif line[0] == 'MEASUREMENT':

                # TODO Measurements

                pass

            elif line[0] == 'MEAS_PCIS':
                raise RuntimeError('error: MEAS_PCIS line must be directly preceded by a MEAS_EARFCNS line.')



    def write_outfile(self):
        pass


def weight(rsrp: float) -> float:
    if rsrp <= -100:
        return 0.15
    elif -100 < rsrp < -80:
        return 0.9
    else:
        return 1.0
