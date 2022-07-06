import unittest
from unittest import TestCase

import os.path

from .. import csvtools as csvt
from .. import association as asc

def rel_dir(path: str):
    return os.path.join(os.path.dirname(__file__), path)

class MyTestCase(TestCase):

    def test_initial_read(self):
        with csvt.CSVWriter(
                rel_dir('../../Mesures_tests/tests/assoc/out_init_read.csv'),
                asc.CellAssociator._HEADER
        ) as out:
            assoc = asc.CellAssociator(
                rel_dir('../../Mesures_tests/C208_10_DR10143732-M1_nz_phone_1.csv'),
                rel_dir('../../Mesures_tests/sites_SFR.csv'),
                rel_dir('../../Mesures_tests/tests/assoc/out_init_read.csv')
            )
            assoc._initial_read(out)

    def test_read_antennas(self):
        with csvt.CSVWriter(
                rel_dir('../../Mesures_tests/tests/assoc/out_read_ant.csv'),
                asc.CellAssociator._HEADER
        ) as out:
            assoc = asc.CellAssociator(
                rel_dir('../../Mesures_tests/C208_10_DR10143732-M1_nz_phone_1.csv'),
                rel_dir('../../Mesures_tests/sites_SFR.csv'),
                rel_dir('../../Mesures_tests/tests/assoc/out_init_read.csv')
            )
            assoc._read_antennas(out)

    def test_process_geometry(self):
        with csvt.CSVWriter(
                rel_dir('../../Mesures_tests/tests/assoc/out_read_ant.csv'),
                asc.CellAssociator._HEADER
        ) as out:
            assoc = asc.CellAssociator(
                rel_dir('../../Mesures_tests/C208_10_DR10143732-M1_nz_phone_1.csv'),
                rel_dir('../../Mesures_tests/sites_SFR.csv'),
                rel_dir('../../Mesures_tests/tests/assoc/out_init_read.csv')
            )
            assoc._initial_read(out)
            assoc._read_antennas(out)
            assoc._process_geometry()


if __name__ == '__main__':
    unittest.main()
