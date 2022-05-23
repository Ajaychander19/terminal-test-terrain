from unittest import TestCase

import os
import os.path

from .. import xcalyzer as xcz
from ..constantPath import getPathText


def rel_dir(path: str):
    return os.path.join(os.path.dirname(__file__), path)


class TestXcalyzer(TestCase):

    FKEYS = [
        'BCCH:BCH', 'BCCH:DL_SCH', 'PCCH',
        'DL CCCH', 'DL DCCH', 'UL CCCH', 'UL DCCH'
    ]

    def setUp(self) -> None:

        # Removing files before each test.
        ls = os.listdir(getPathText(''))

        for dir_entry in ls:
            dpath = os.path.join(getPathText(''), dir_entry)

            # Removing directory entries which are files.
            if os.path.isfile(dpath):
                os.remove(dpath)

    def test_parse_aof(self):
        conv = xcz.XcalConverter(rel_dir('../../donnees/DR10143732-M1.aof'))
        conv.parse_aof()

    def test_produce_pcap(self):

        conv = xcz.XcalConverter(rel_dir('../../donnees/DR10143732-M1.aof'))
        conv.parse_aof()

        for f in self.FKEYS:
            conv.produce_pcap(f)

    def test_merge_pcap(self):

        conv = xcz.XcalConverter(rel_dir('../../donnees/DR10143732-M1.aof'))
        conv.parse_aof()

        files = []

        for f in self.FKEYS:
            conv.produce_pcap(f)
            files.append(conv.get_file_name(f, 'pcap'))

        xcz.merge_pcap(files, 'test_merge.pcap')

    def test_reorder_pcap(self):

        conv = xcz.XcalConverter(rel_dir('../../donnees/DR10143732-M1.aof'))
        conv.parse_aof()

        files = []

        for f in self.FKEYS:
            conv.produce_pcap(f)
            files.append(conv.get_file_name(f, 'pcap'))

        xcz.merge_pcap(files, 'test_merge.pcap')

        xcz.reorder_pcap('test_merge.pcap', 'test_merge_ord.pcap')
