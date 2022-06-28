import os.path
import unittest
from unittest import TestCase

from .. import cartoradio as cr


def rel_dir(path: str):
    return os.path.join(os.path.dirname(__file__), path)


class MyTestCase(TestCase):

    def test_process_cartoradio(self):
        sites = rel_dir('../../donnees/Sites_Cartoradio.csv')
        ant = rel_dir('../../donnees/Antennes_Emetteurs_Bandes_Cartoradio.csv')
        out = rel_dir('../../Mesures_tests')

        cr.process_cartoradio(sites, ant, out)

    def test_giga_file(self):
        sites = rel_dir('../../donnees/Sites_Cartoradio_bretagne.csv')
        ant = rel_dir('../../donnees/Antennes_Emetteurs_Bandes_Cartoradio_bretagne.csv')
        out = rel_dir('../../Mesures_tests')

        cr.process_cartoradio(sites, ant, out)

if __name__ == '__main__':
    unittest.main()
