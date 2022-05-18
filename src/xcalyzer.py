"""This module is dedicated to the analysis of AOF files produced by Accuver Xcal."""
import os.path

from constantPath import getPathText, getWireshark

import subprocess

# Constants
_DICT_DISSECTOR = {
    'temporary': 148,   # FIXME Unknown code for this protocol.
    'BCCH:DL_SCH': 149,
    'PCCH': 150,
    'DL CCCH': 151,
    'UL CCCH': 152,
    'DL DCCH': 153,
    'UL DCCH': 154
}


def get_dissector_num(diss_name: str):
    return _DICT_DISSECTOR[diss_name]


def read_line(f):
    return f.readline().split('|')


def syntax_error(line: int, msg: str):
    raise RuntimeError('Error: line {0}, {1}'.format(line, msg))


# class XcalMessage:
#
#     def __init__(self, date: str, data: str):
#         self._date = date
#         self._data = data
#
#     def _get_date(self):
#         return self._date
#
#     def _get_data(self):
#         return self._data
#
#     date = property(_get_date)
#     data = property(_get_data)


class XcalConverter:
    
    # Constants.

    DICT_FILES_NAMES = {
        'temporary': 'BCCH_BCH_148',   # FIXME Unknown code for this protocol.
        'BCCH:DL_SCH': 'BCCH_DL_149',
        'PCCH': 'PCCH_DL_150',
        'DL CCCH': 'CCCH_DL_151',
        'UL CCCH': 'CCCH_UL_152',
        'DL DCCH': 'DCCH_DL_153',
        'UL DCCH': 'DCCH_UL_154'
    }

    def __init__(self, path: str):
        # self._files = {
        #     'BCCH:DL_SCH': None,
        #     'PCCH': None,
        #     'DL DCCH': None,
        #     'UL DCCH': None,
        # }
        #self._gps = []

        self._path = path
        self._phone_id = 'phone_1'        # FIXME Temporary ID
        
        # File dictionnary.
        self._files = {
            'temporary': None,  # FIXME Unknown code for this protocol.
            'BCCH:DL_SCH': None,
            'PCCH': None,
            'DL CCCH': None,
            'DL DCCH': None,
            'UL CCCH': None,
            'UL DCCH': None,
        }

    def parse_aof(self):

        state = 0  # Current automata state.
        line_num = 1  # Line number.

        # Opening AOF file.
        with open(self._path, 'r') as aof:

            try:

                line = read_line(aof)  # Current line.

                # Parsing automata
                while line[0] != '' and state != 7:

                    # First word of the line.
                    first = line[0]
                    l_len = len(line)

                    if state == 0:  # Initial state.

                        if first == '<AOF_Information_START>\n':
                            state = 1
                        else:
                            syntax_error(line_num, 'Invalid file starting "{}"'.format(first))

                    elif state == 1:  # Skipping AOF info section.

                        if first == '<AOF_Information_END>\n':
                            state = 2

                    elif state == 2:  # Description section start.

                        if first == '<Description Start>\n':
                            state = 3
                        else:
                            syntax_error(line_num, 'Invalid description start "{}"'.format(first))

                    elif state == 3:  # Getting phone ID, opening temporary files.

                        # if first == '<Description End>\n':
                        #    state = 4

                        # TODO Get phone ID.
                        if True:

                            self._phone_id = 'phone_1'

                            # Opening files.
                            for k in self._files.keys():
                                path = getPathText(
                                    '{0}_{1}.txt'.format(self.DICT_FILES_NAMES[k], self._phone_id)
                                )
                                self._files[k] = open(path, 'w')

                            state = 4

                    elif state == 4:  # Description section skip.

                        if first == '<Description End>\n':
                            state = 5

                    elif state == 5:  # Content section start.

                        if first == '<Content Start>\n':
                            state = 6
                        else:
                            syntax_error(line_num, 'Invalid content start "{}"'.format(first))

                    elif state == 6:  # Content parsing.

                        if first == 'QCLTE_RRCMSG_V2':

                            # Check if the line has a valid length.
                            if l_len < 13:
                                syntax_error(line_num, "13 columns expected, {} found.".format(l_len))

                            msg_type = line[6]  # Message type.

                            # Check if the message type is valid.
                            if msg_type not in self._files.keys():
                                syntax_error(line_num, "Invalid message type : {}".format(msg_type))

                            # Adding the message to the corresponding list.
                            self._files[msg_type].write('{0}\n0000 {1}\n'.format(line[1], line[12]))

                        elif first == 'GPS':
                            pass  # TODO Parse GPS message
                        elif first == 'QCLTE_PSCELL':
                            pass  # TODO Parse PSCELL
                        elif first == '<Content End>\n':  # File ending.
                            state = 7  # Final state because of EOF.

                    line = read_line(aof)  # Next line.
                    line_num += 1

            finally:

                # Closing files.
                for k in self._files.keys():
                    f = self._files[k]

                    # Checking if the file is properly open...
                    if f:
                        f.close()

        # Check if we are in the final state after finishing the parsing.
        # NOTE: this code is reachable, despite PyCharm warnings
        # You can for example remove <Content End> in the AOF file to execute it...
        if state != 7:
            syntax_error(line_num, 'Unexpected End Of File, state={}.'.format(state))

    def produce_pcap(self, fkey: str):

        # Controlling fkey.
        if fkey not in self.DICT_FILES_NAMES.keys():
            raise RuntimeError('Error : invalid file key : {}.'.format(fkey))

        input_txt = getPathText(self.get_file_name(fkey, 'txt'))
        output_pcap = getPathText(self.get_file_name(fkey, 'pcap'))

        # Preparing text2pcap call.
        t2p_argc = [
            getWireshark('text2pcap'),          # Wireshark command path.
            '-t', '%F %H:%M:%S.',                      # Time format to use in the pcap file.
            input_txt,                          # Input .txt file.
            output_pcap,                        # Output .pcap file.
            '-l', str(get_dissector_num(fkey))  # Number of the dissector to be called.
        ]

        # Calling text2pcap
        subprocess.check_call(t2p_argc)


    def reorder_pcap(self, fname: str, dest: str):

        input_file = getPathText(fname)
        output_file = getPathText(dest)

        # Preparing reordercap call.
        rcap_argc = [
            getWireshark('reordercap'),     # Command path
            '-n',                           # Produce a file only if a reordering has been done.
            input_file,
            output_file
        ]

        # Calling reordercap
        subprocess.check_call(rcap_argc)

    def merge_pcap(self, paths: list, dest: str):

        # Preparing mergecap
        output_file = getPathText(dest)

        # Initial arguments list.
        mcap_argc = [
            getWireshark('mergecap'),
            '-a',               # Concat files.
            '-w', output_file   # File to write.
        ]

        # Adding files paths to the argument list.
        for p in paths:
            mcap_argc.append(getPathText(p))

        # Calling mergecap
        subprocess.check_call(mcap_argc)

    def get_file_name(self, fkey: str, ext: str) -> str:

        # Controlling fkey.
        if fkey not in self.DICT_FILES_NAMES.keys():
            raise RuntimeError('Error : invalid file key : {}.'.format(fkey))

        return '{0}_{1}.{2}'.format(self.DICT_FILES_NAMES[fkey], self._phone_id, ext)

    def _get_phone_id(self):
        return self._phone_id

    # Class properties.
    phone_id = property(_get_phone_id)
