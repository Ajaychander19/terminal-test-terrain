from unittest import TestCase

import os.path

from .. import xcalyzer as xcz


def rel_dir(path: str):
    return os.path.join(os.path.dirname(__file__), path)


class TestXcalyzer(TestCase):
    def test_parse_aof(self):
        xcz.parse_aof(rel_dir('../../donnees/DR10143732-M1.aof'))
