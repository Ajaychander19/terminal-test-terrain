"""This module is dedicated to the analysis of AOF files produced by Accuver Xcal."""

from constantPath import getPathText, getWireshark, getfileName

# Needed library : pycrate
from pycrate_asn1dir import RRCLTE

import binascii
import json
import subprocess

# Constants
_DICT_DISSECTOR = {
    'BCCH:BCH': 148,
    'BCCH:DL_SCH': 149,
    'PCCH': 150,
    'DL CCCH': 151,
    'UL CCCH': 152,
    'DL DCCH': 153,
    'UL DCCH': 154
}


def get_dissector_num(diss_name: str) -> int:
    """Associates a dissector name with the corresponding dissector number.

    Parameters:
        diss_name: the dissector name.

    Returns:
        The corresponding dissector number.
    """
    return _DICT_DISSECTOR[diss_name]


def read_line(f) -> list:
    """Read a line from an AOF file.

    Parameters:
        f: an AOF file.

    Returns:
        A list of values, following CSV separators found in the current line.
    """
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
        'BCCH:BCH': 'BCCH_BCH_148',
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
        self._line_num = 1

        self._last_lat = '0.0'
        self._last_lng = '0.0'

        self._pci = '0'
        self._earfcn = '0'

        self._mcc = None
        self._mnc = None

        self._last_payload = None
        self._last_msg_type = None

        # File dictionnary.
        self._files = {
            'BCCH:BCH': None,
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

        fname = getfileName(self._path)[0]

        # Opening AOF file.
        with open(self._path, 'r') as aof, open('C_{}_tmp.json'.format(fname), 'w') as json_final:

            json_list = []

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
                            syntax_error(self._line_num, 'Invalid file starting "{}"'.format(first))

                    elif state == 1:  # Skipping AOF info section.

                        if first == '<AOF_Information_END>\n':
                            state = 2

                    elif state == 2:  # Description section start.

                        if first == '<Description Start>\n':
                            state = 3
                        else:
                            syntax_error(self._line_num, 'Invalid description start "{}"'.format(first))

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
                            syntax_error(self._line_num, 'Invalid content start "{}"'.format(first))

                    elif state == 6:  # Content parsing.

                        if first == 'QCLTE_RRCMSG_V2' or first == 'QCLTE_RRCMSG':

                            is_v2 = first == 'QCLTE_RRCMSG_V2'

                            self._pci = line[8 if is_v2 else 7]
                            self._earfcn = line[9 if is_v2 else 8]

                            # Check if the line has a valid length.
                            if l_len < 13:
                                syntax_error(self._line_num, "13 columns expected, {} found.".format(l_len))

                            msg_type = line[6 if is_v2 else 5]  # Message type.
                            payload = line[12 if is_v2 else 11] # Message payload.

                            # Check if the message type is valid.
                            if msg_type not in self._files.keys():
                                syntax_error(self._line_num, "Invalid message type : {}".format(msg_type))

                            # Adding the message to the corresponding file.
                            self._files[msg_type].write(
                                '{0}\n0000 {1}\n'.format(line[1], payload))

                            asn_payload = self.produce_asn1(msg_type, payload)

                            if asn_payload != {}:
                                pdata = asn_payload['message']['c1']

                                if 'measurementReport' in pdata.keys():
                                    self._last_payload = asn_payload
                                elif 'systemInformationBlockType1' in pdata.keys():
                                    json_list.append(self.process_payload(asn_payload))

                        elif first == 'GPS':

                            self._last_lng = line[2]
                            self._last_lat = line[3]

                            if self._last_payload:
                                processed_payload = self.process_payload(self._last_payload)
                                if processed_payload != {}:
                                    json_list.append(processed_payload)

                            # TODO Parse GPS message

                        elif first == 'QCLTE_PSCELL':
                            pass  # TODO Parse PSCELL
                        elif first == '<Content End>\n':  # File ending.
                            state = 7  # Final state because of EOF.

                    line = read_line(aof)  # Next line.
                    self._line_num += 1

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
                syntax_error(self._line_num, 'Unexpected End Of File, state={}.'.format(state))

            json.dump(json_list, json_final, indent=4)

    def produce_asn1(self, msg_type: str, payload: str):
        # Extracting RRC message data.

        # Choosing message object.
        msg_obj = None
        if msg_type == 'BCCH:DL_SCH':
            msg_obj = RRCLTE.EUTRA_RRC_Definitions.BCCH_DL_SCH_Message
        elif msg_type == 'UL DCCH':
            msg_obj = RRCLTE.EUTRA_RRC_Definitions.UL_DCCH_Message
        else:
            return {}

        # Loading payload...
        msg_obj.from_uper(
            binascii.unhexlify(''.join(payload.split(' ')).strip()))

        # Decoding message data.
        return json.loads(msg_obj.to_json())


    def process_payload(self, msg_data: dict) -> dict:

        # Processing message data.

        packet_data = msg_data['message']['c1']

        # If SIB1...
        if 'systemInformationBlockType1' in packet_data.keys():

            # Contains the cellID and the TAC.
            cell_access_info = packet_data['systemInformationBlockType1']['cellAccessRelatedInfo']

            # Contains PLMN's MCC and MNC.
            plmn_info = cell_access_info['plmn-IdentityList'][0]['plmn-Identity']

            mcc = ''.join([str(i) for i in plmn_info['mcc']])
            mnc = ''.join([str(i) for i in plmn_info['mnc']])

            if not self._mcc:
                self._mcc = mcc

            if not self._mnc:
                self._mnc = mnc

            return {
                'SIB': {
                    'TAC': cell_access_info['trackingAreaCode'],
                    'CellID': cell_access_info['cellIdentity'],
                    'PCI': self._pci,
                    'EARFCN': self._earfcn,
                    'geolocation': {
                        'lat': self._last_lat,
                        'lng': self._last_lng,
                    },
                    'mcc': mcc,
                    'mnc': mnc,
                }
            }

        elif 'measurementReport' in packet_data.keys():     # If MeasurementReport...

            meas_data \
                = packet_data['measurementReport']['criticalExtensions']['c1']['measurementReport-r8']['measResults']

            # Current cell measurement results.
            pcell_result = meas_data['measResultPCell']

            # Neighbours cells measurement result.
            # FIXME Cells without neighbours can exist.

            rsrp_offset = -1000

            if 'measResultNeighCells' in meas_data.keys():
                ncells_result = meas_data['measResultNeighCells']['measResultListEUTRA']

                # Calculating neighborMax_RSRP.
                ncells_max_rsrp = ncells_result[0]['measResult']['rsrpResult']

                ncells_rsrps = []

                for ncell in ncells_result:
                    ncell_rsrp = ncell['measResult']['rsrpResult']
                    ncells_rsrps.append(ncell_rsrp)
                    ncells_max_rsrp = max(ncells_max_rsrp, ncell_rsrp)

                rsrp_offset = (sum(ncells_rsrps) / len(ncells_rsrps)) - ncells_max_rsrp

            return {
                'Mesurement': {
                    'PCI': self._pci,
                    'EARFCN': self._earfcn,
                    'Geolocation': {
                        'lat': self._last_lat,
                        'lng': self._last_lng,
                    },
                    'RSRP': pcell_result['rsrpResult'],
                    'neighbourMax_RSRP': rsrp_offset,
                }
            }

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
