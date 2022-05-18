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
    """This class is used to analyze Accuver Xcal AOF file format. It provides few methods to
    analyze and convert AOF files in PCAP file. An instance of this class can process one AOF
    file. It can be used to create PCAP files associated with different Wireshark dissectors,
    can merge several PCAP files into one PCAP file, and reorder PCPA file contents. It can also,
    based on the ID of the user equipment used to create AOF file, manage file names.
    """
    
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
        """Class constructor.

        Parameters:
            path: path of the AOF file which will be analyzed.
        """
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
        """Parses the associated AOF file.

        The parsing produce temporary files .txt files, one for each Wireshark
        dissector. These files can be used by text2pcap.

        Raises:
            RuntimeError: if an error occurred during the analysis of the AOF file.
        [WIP]
        """

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
        """Produces a PCAP file following a given dissector key from TXT file with text2pcap. This key corresponds to
        XcalConverter.DICT_FILES_NAMES dictionary keys. The function produces a temporary PCAP file
        related to only one dissector, from a TXT file, corresponding to the key ; the temporary file name is the
        string associated with this key in XcalConverter.DICT_FILES_NAMES.

        Parameters:
            fkey: the corresponding dissector key.

        Raises:
            RuntimeError: if fkey is invalid.
            CalledProcessError: if text2pcap produces an error.
        """

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
        """Reorders a given PCAP temporary file with reordercap. Produces the resulting
        PCAP temporary reordered file.

        Parameters:
            fname: the name of the temporary PCAP source file.
            dest: the name of the temporary PCAP destination file which will be created.

        Raises:
            CalledProcessError: if reordercap produces an error.
        """

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

    def merge_pcap(self, names: list, dest: str):
        """Concatenates several given PCAP temporary files into another given PCAP temporary file with mergecap.

        Parameters:
            names: name of temporary files to concatenate.
            dest: name of the temporary output file.

        Raises:
            CalledProcessError: if mergecap produces an error.

        """
        # Preparing mergecap
        output_file = getPathText(dest)

        # Initial arguments list.
        mcap_argc = [
            getWireshark('mergecap'),
            '-a',               # Concat files.
            '-w', output_file   # File to write.
        ]

        # Adding files paths to the argument list.
        for n in names:
            mcap_argc.append(getPathText(n))

        # Calling mergecap
        subprocess.check_call(mcap_argc)

    def get_file_name(self, fkey: str, ext: str) -> str:
        """Associates a given key of XcalConverter.DICT_FILES_NAMES with the corresponding
        temporary file name, from the phone_id attribute, and a given file extension.

        Parameters:
            fkey: key from XcalConverter.DICT_FILES_NAMES.
            ext: file extension.

        Returns:
            The corresponding temporary file name.

        Raises:
            RuntimeError: if fkey is not present in XcalConverter.DICT_FILES_NAMES.
        """
        # Controlling fkey.
        if fkey not in self.DICT_FILES_NAMES.keys():
            raise RuntimeError('Error : invalid file key : {}.'.format(fkey))

        return '{0}_{1}.{2}'.format(self.DICT_FILES_NAMES[fkey], self._phone_id, ext)

    def _get_phone_id(self):
        """
            Getter of the phone_id attribute associated to the AOF file.

            Returns:
                the phone ID attribute
        """
        return self._phone_id

    # Class properties.
    phone_id = property(_get_phone_id)
