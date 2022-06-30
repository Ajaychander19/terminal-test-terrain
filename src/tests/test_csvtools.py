import unittest
from unittest import TestCase

import os.path

from .. import csvtools as csv


def rel_dir(path: str):
    return os.path.join(os.path.dirname(__file__), path)


class TestCSVWriter(TestCase):

    def test_header_syntax1(self):

        # Empty key

        header = {
            '': ['aaa', 'bbb', '123'],
            'test42': ['test1', 'test2']
        }

        self.assertRaises(RuntimeError, lambda: csv.CSVWriter('test', header))

    def test_header_syntax2(self):

        # Empty field name

        header = {
            '123': ['', 'bbb', '123'],
            'test42': ['test1', 'test2']
        }

        self.assertRaises(RuntimeError, lambda: csv.CSVWriter('test', header))

    def test_header_syntax3(self):

        # Malformed key

        header = {
            '12+/3': ['test', 'bbb', '123'],
            'test42': ['test1', 'test2']
        }

        self.assertRaises(RuntimeError, lambda: csv.CSVWriter('test', header))

    def test_header_syntax4(self):

        # Malformed field name

        header = {
            '123': ['test', 'bbb', '123'],
            'test42': ['te/*qsxst1', 'test2']
        }

        self.assertRaises(RuntimeError, lambda: csv.CSVWriter('test', header))

    def test_header_syntax5(self):

        # Correct field name with underscore.

        header = {
            '123': ['test', 'bbb', '123'],
            'test42': ['te_st1', 'test2']
        }

        csv.CSVWriter('test', header)

    def test_header_syntax6(self):

        # Correct key with underscore.

        header = {
            '123': ['test', 'bbb', '123'],
            'test_42': ['test1', 'test2']
        }

        csv.CSVWriter('test', header)

    def test_header_key_type1(self):

        # Invalid key type.

        header = {
            123: ['test', 'bbb', '123'],
            'test42': ['te_st1', 'test2']
        }

        self.assertRaises(TypeError, lambda: csv.CSVWriter('test', header))

    def test_header_key_type2(self):

        # Invalid key type.

        header = {
            145.0: ['aaa', 'bbb', '123'],
            'test42': ['te_st1', 'test2']
        }

        self.assertRaises(TypeError, lambda: csv.CSVWriter('test', header))

    def test_header_field_type1(self):

        # Invalid field name type.

        header = {
            '123': [dict(), 'bbb', '123'],
            'test42': ['te_st1', 'test2']
        }

        self.assertRaises(TypeError, lambda: csv.CSVWriter('test', header))

    def test_header_field_type2(self):

        # Invalid file name type.

        header = {
            '123': [0, 'bbb', '123'],
            'test42': ['te_st1', 'test2']
        }

        self.assertRaises(TypeError, lambda: csv.CSVWriter('test', header))

    def test_header_empty_field(self):

        # Empty header field.

        header = {
            '123': [],
            'test42': ['te_st1', 'test2']
        }

        self.assertRaises(RuntimeError, lambda: csv.CSVWriter('test', header))

    def test_header_entry_type(self):

        # Invalid row type.

        header = {
            '123': 0,
            'test42': ['te_st1', 'test2']
        }

        self.assertRaises(TypeError, lambda: csv.CSVWriter('test', header))

    def test_insert_invalid_key(self):

        # Attempting to insert a bad key.

        header = {
            'key1': ['field1', 'field2'],
            'key2': ['f1', 'f2', 'f3', 'f4'],
            'key3': ['fa']
        }

        with csv.CSVWriter(rel_dir('../../Mesures_tests/tests/csv/test_inval_key.csv'), header) as writer:
            self.assertRaises(KeyError, lambda: writer.write_row(['key4', '50', '13']))

    def test_insert_uncomplete_row1(self):

        # Empty row

        header = {'key1': ['field1']}

        with csv.CSVWriter(rel_dir('../../Mesures_tests/tests/csv/unc_row1.csv'), header) as writer:
            self.assertRaises(RuntimeError, lambda: writer.write_row([]))

    def test_insert_uncomplete_row2(self):

        # One element row.

        header = {'key1': ['field1']}

        with csv.CSVWriter(rel_dir('../../Mesures_tests/tests/csv/unc_row2.csv'), header) as writer:
            self.assertRaises(RuntimeError, lambda: writer.write_row(['key1']))

    def test_insert_invalid_value(self):

        # Typo in value.

        header = {'key1': ['field1', 'field2']}

        with csv.CSVWriter(rel_dir('../../Mesures_tests/tests/csv/inv_val.csv'), header) as writer:
            self.assertRaises(RuntimeError, lambda: writer.write_row(['key1', 'test_123', 'ok |']))

    def test_insert_invalid_key_syntax(self):

        header = {'key1': ['field1', 'field2']}

        with csv.CSVWriter(rel_dir('../../Mesures_tests/tests/csv/inv_key_synt.csv'), header) as writer:
            self.assertRaises(RuntimeError, lambda: writer.write_row(['key$1', 'test_123', 'ok']))

    def test_produce_file1(self):

        header = {
            'user': ['first_name', 'last_name', 'username'],
            'device': ['device_name', 'model']
        }

        with csv.CSVWriter(rel_dir('../../Mesures_tests/tests/csv/test_file1.csv'), header) as writer:
            writer.write_row(['user', 'killian', 'callac', 'killian2001'])
            writer.write_row(['user', 'john', 'doe', 'jdoe'])
            writer.write_row(['device', 'google pixel', 'pixel 5'])
            writer.write_row(['user', 'truc', 'bidule', 'chouette'])
            writer.write_row(['device', 'samsung galaxy', 'galaxy s6'])

    def test_produce_file2(self):
        header = {
            'EARFCN': ['EARFCN1', 'EARFCN2', 'EARFCN3', 'Other_EARFCNs'],
            'PCI': ['PCI1', 'PCI2', 'PCI3', 'Other_PCIs'],
            'RSRP': ['RSRP1', 'RSRP2', 'RSRP3', 'Other_RSRPs']
        }

        with csv.CSVWriter(rel_dir('../../Mesures_tests/tests/csv/test_file2.csv'), header) as writer:
            writer.write_row(['EARFCN', '1501', '1501', '1501', '6300', '1501'])
            writer.write_row(['PCI', '80', '81', '82', '83', '83'])
            writer.write_row(['RSRP', '-60', '-50', '-40', '', '-50'])
            writer.write_row(['RSRP', '-65', '-55', '-40', '', '-55'])
            writer.write_row(['RSRP', '-68', '-58', '-40', '', '-58'])


class TestCSVReader(TestCase):

    def test_correct1(self):
        with csv.CSVReader(rel_dir('../../Mesures_tests/tests/csv_reader/correct1.csv')) as crd:
            assert crd.read_line() == ['CONTENT1', 'truc', 'bidule', 'chouette.123']
            assert crd.read_line() == ['CONTENT2', '-89', '10.2458']

    def test_correct2(self):
        with csv.CSVReader(rel_dir('../../Mesures_tests/tests/csv_reader/correct2.csv')) as crd:
            assert crd.read_line() == ['CONTENT1', '', '', 'chouette.123']
            assert crd.read_line() == ['CONTENT1', '30', '', '50.123']

    def test_header1(self):
        with csv.CSVReader(rel_dir('../../Mesures_tests/tests/csv_reader/correct1.csv')) as crd:
            assert crd.get_header() == {
                'CONTENT1': ['A', 'b', 'C_D'],
                'CONTENT2': ['a', '123_4']
            }

    def test_header2(self):
        with csv.CSVReader(rel_dir('../../Mesures_tests/tests/csv_reader/correct2.csv')) as crd:
            assert crd.get_header() == {
                'CONTENT1': ['123', '456', '789'],
                'CONT_ENT2': ['truc']
            }

    def test_invalid_key(self):
        self.assertRaises(
            RuntimeError, lambda: csv.CSVReader(
                rel_dir('../../Mesures_tests/tests/csv_reader/inv_key.csv')).open_file())

    def test_invalid_key_syntax(self):
        self.assertRaises(
            RuntimeError, lambda: csv.CSVReader(
                rel_dir('../../Mesures_tests/tests/csv_reader/inv_key_synt.csv')).open_file())

    def test_invalid_field(self):
        self.assertRaises(
            RuntimeError, lambda: csv.CSVReader(
                rel_dir('../../Mesures_tests/tests/csv_reader/inv_field.csv')).open_file())

    def test_invalid_value(self):
        self.assertRaises(
            RuntimeError, lambda: csv.CSVReader(
                rel_dir('../../Mesures_tests/tests/csv_reader/inv_value.csv')).open_file())


if __name__ == '__main__':
    unittest.main()
