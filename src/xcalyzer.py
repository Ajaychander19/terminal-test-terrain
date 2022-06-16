"""This module is dedicated to the analysis of AOF files produced by Accuver Xcal."""

from constantPath import getPathText, getfileName

import datetime
import json
import math
import os
import shutil
import itertools

import pcaputils
import csvtools

import pandas as pd

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


def extend_dict(d1: dict, d2: dict):
    for k in d2.keys():
        if k in d1.keys():
            d1[k].extend(d2[k])
        else:
            d1[k] = d2[k]


def append_dict(d1: dict, d2: dict):
    for k in d2.keys():
        if k not in d1.keys():
            d1[k] = []
        d1[k].append(d2[k])


def insert_data(d1: dict, d2: dict, l: int):
    for k in d1.keys():
        d1[k].extend([None] * l if k not in d2.keys() else d2[k])


def replace_data(d1: dict, d2: dict, index: int, l: int):
    for k in d1.keys():
        if k in d2.keys():
            for i in range(index, index + l):
                if d1[k][i] is None:
                    d1[k][i] = d2[k][i - index]



def get_tstamp(date: str) -> float:
    return datetime.datetime.fromisoformat(date).timestamp()


def generate_estimator(pos_a: (float, float), pos_b: (float, float), t1: float, t2: float):
    delta_x = pos_b[0] - pos_a[0]
    delta_y = pos_b[1] - pos_a[1]
    delta_t = t2 - t1

    if delta_t == 0:
        return lambda t: pos_a
    else:
        return lambda t: (
            ((t - t1) / delta_t) * delta_x + pos_a[0],
            ((t - t1) / delta_t) * delta_y + pos_a[1]
        )


def estimate_pos(d: dict, est):
    if d:
        tstamps = d['timestamp']

        for i in range(len(tstamps)):
            pos = est(tstamps[i])
            d['lat'][i] = pos[0]
            d['lng'][i] = pos[1]


def produce_json(d: dict, json_file):
    """Produces in the JSON file an ASN1 entry from a given ASN1 dictionary.

    Parameters:
        asn1: ASN1 dictionary.
        json_file: JSON file to write in.
    """
    asn1_json = json.dumps(d, indent=4)
    prod_json = ''

    for asn_line in asn1_json.splitlines(keepends=True):
        prod_json += '    ' + asn_line

    json_file.write(prod_json)


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

    # CELLINFO dataframe structure.
    _CINFO_DATAFRAME_DICT = {
        'id': [], 'name': [], 'timestamp': [], 'lat': [],
        'lng': [], 'tac': [], 'cid': [], 'mcc': [], 'mnc': []
    }

    # Serving EARFCN/PCI dataframe structure.
    _SERV_DATAFRAME_DICT = {
        'id': [], 'name': [], 'timestamp': [], 'lat': [],
        'lng': [], 'earfcn': [], 'pci': []
    }

    # Measurement dataframe structure.
    _MEAS_DATAFRAME_DICT = {
        'id': [], 'meas_id': [], 'name': [], 'timestamp': [], 'lat': [],
        'lng': [], 'earfcn': [], 'pci': [], 'meas_name': []
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
        # self._gps = []

        self._path = path
        self._phone_id = 'phone_1'  # FIXME Temporary ID
        self._line_num = 1

        self._pci = '0'
        self._earfcn = '0'

        self._earfcns = []
        self._pcis = []

        self._data_dict = {
            'name': [], 'timestamp': [], 'lat': [], 'lng': [],  # Common fields
            'earfcn': [], 'pci': [],                            # Serving Cell
            'tac': [], 'cid': [], 'mcc': [], 'mnc': [],         # Cell information
            'meas_name': []                                     # Measurement
        }

        self._id = 0
        self._meas_id = 0

        self._tac = '0'
        self._cid = '0'

        self._mcc = '0'
        self._mnc = '0'

        self._content_start = 0

        self._rsrp = 0.0

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

    def process(self, outdir: str):
        """Processes the AO0F file.

        Calls the following subfunctions:
            - parse_aof: parses the AOF file, and produces the JSON output file.
            - produce_pcaps: produces a PCAP file for each Wireshark dissector used.
            - merge_pcaps: merges PCAP files produced by produce_pcaps.
            - reorder_pcap: reorder the produced PCAP file.
            - finalize: produces final PCAP and JSON files.

        Parameters:
            outdir: output directory.

        """
        self.parse_aof()
        self.produce_pcaps()
        self.merge_pcaps()
        self.reorder_pcap()
        self.finalize(outdir)

    def parse_aof(self):
        """Parses the associated AOF file.

        The parsing produce temporary files .txt files, one for each Wireshark
        dissector. These files can be used by text2pcap.

        Raises:
            RuntimeError: if an error occurred during the analysis of the AOF file.
        [WIP]
        """

        state = 0  # Current automata state.

        fname = getfileName(self._path)

        self.first_read()
        print('first_read')
        self.second_read()
        print('second_read')
        # Producing closing char in JSON file.
        # json_final.write('\n]\n')

    def first_read(self):

        # Opening AOF file.
        with open(self._path, 'r') as aof:

            try:

                line = read_line(aof)  # Current line.

                # Used to properly produce commas which separate JSON entries.
                first_entry = True

                state = 0

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

                    elif state == 3:  # Description section skip.

                        if first == '<Description End>\n':
                            state = 4

                    elif state == 4:  # Content section start.

                        if first == '<Content Start>\n':
                            state = 5
                            self._content_start = self._line_num
                        else:
                            syntax_error(self._line_num, 'Invalid content start "{}"'.format(first))

                    elif state == 5:  # Getting phone ID, opening temporary files.

                        # if first == '<Description End>\n':
                        #    state = 4

                        # TODO Get phone ID (and replace if condition).
                        if True:

                            self._phone_id = 'phone_1'

                            # Opening files.
                            for k in self._files.keys():
                                path = getPathText(
                                    '{0}_{1}.txt'.format(self.DICT_FILES_NAMES[k], self._phone_id)
                                )
                                self._files[k] = open(path, 'w')

                            state = 6

                    elif state == 6:  # Content parsing.

                        tstamp = 0

                        if first != '<Content End>\n':

                            if l_len < 2:
                                syntax_error(self._line_num, "2 columns minimum expected, {} found.".format(l_len))

                            tstamp = get_tstamp(line[1])

                        if first == 'QCLTE_RRCMSG_V2' or first == 'QCLTE_RRCMSG':

                            is_v2 = first == 'QCLTE_RRCMSG_V2'

                            # self._pci = line[8 if is_v2 else 7]
                            # self._earfcn = line[9 if is_v2 else 8]

                            # Check if the line has a valid length.
                            if l_len < 13:
                                syntax_error(self._line_num, "13 columns expected, {} found.".format(l_len))

                            msg_type = line[6 if is_v2 else 5]  # Message type.
                            payload = line[12 if is_v2 else 11]  # Message payload.

                            # Check if the message type is valid.
                            if msg_type not in self._files.keys():
                                syntax_error(self._line_num, "Invalid message type : {}".format(msg_type))

                            # Adding the message to the corresponding file.
                            self._files[msg_type].write(
                                '{0}\n0000 {1}\n'.format(line[1], payload))

                        elif first == 'GPS':

                            if l_len < 9:
                                syntax_error(self._line_num, '8 columns expected, {} found.'.format(l_len))

                            # produce_json(to_produce, json_final)

                        elif first == 'QCLTE_PSCELL':

                            if l_len < 16:
                                syntax_error(self._line_num, "16 columns expected, {} found.".format(l_len))

                            serving_earfcn = int(line[2])
                            serving_pci = int(line[4])

                            # TODO Calculate CINR
                            serving_cinr = 0.0
                            #
                            # # Adding serving cell information.
                            # append_dict(
                            #     self._tmp_serv_frame,
                            #     {
                            #         'id': self._id, 'name': 'MEASURE_SERVING', 'timestamp': tstamp, 'lat': 0, 'lng': 0,
                            #         'earfcn': serving_earfcn, 'pci': serving_pci
                            #     }
                            # )
                            #
                            # self._id += 1
                            #
                            # # Adding serving cell measurements.
                            # # extend_dict(
                            # #     self._tmp_meas_frame,
                            # #     {
                            # #         'id': [self._id + i for i in range(4)],
                            # #         # 'meas_id': [self._meas_id] * 4,
                            # #         'name': ['MEASUREMENT'] * 4,
                            # #         'timestamp': 4 * [tstamp],
                            # #         'lat': [None] * 4, 'lng': [None] * 4,
                            # #         'earfcn': [serving_earfcn] * 4,
                            # #         'pci': [serving_pci] * 4,
                            # #         'meas_name': ['RSRP', 'RSQR', 'RSSI', 'CINR'],
                            # #         'value': [serving_rsrp, serving_rsrq, serving_rssi, serving_cinr]
                            # #     }
                            # # )
                            #
                            self._earfcns.append(serving_earfcn)
                            self._pcis.append(serving_pci)
                            #
                            # self._id += 4

                            # if serving_rsrp != '':
                            #    self._rsrp = math.floor(140 + float(serving_rsrp)) + 1

                        elif first == 'QCLTE_CELLINFO':

                            if l_len < 16:
                                syntax_error(self._line_num, "16 columns expected, {} found.".format(l_len))

                            # mcc = line[14]
                            # mnc = line[15]
                            #
                            # pci = line[2]
                            # earfcn = line[3]
                            #
                            # cid = int(line[9])
                            # if cid > 0xFFFFFFFF:
                            #     syntax_error(self._line_num, 'CID should be lower than 268435456.')
                            #
                            # cid_str = '{0:08x}'.format(cid)
                            # cid = '{0}:{1}:{2}:{3}'.format(
                            #     cid_str[0:2], cid_str[2:4], cid_str[4:6], cid_str[6:8])
                            #
                            # tac = int(line[12])
                            # if tac > 0xFFFF:
                            #     syntax_error(self._line_num, 'TAC should be lower than 65536')
                            #
                            # tac_str = '{0:04x}'.format(tac)
                            # tac = '{0}:{1}'.format(tac_str[0:2], tac_str[2:4])
                            #
                            # append_dict(
                            #     self._tmp_cinfo_frame, {
                            #         'id': self._id, 'name': 'CELLINFO', 'timestamp': tstamp,
                            #         'lat': None, 'lng': None, 'tac': tac, 'cid': cid,
                            #         'mcc': mcc, 'mnc': mnc
                            #     }
                            # )
                            #
                            # self._id += 1

                            # if first_entry:
                            #     first_entry = False
                            # else:
                            #     json_final.write(',\n')

                            # to_produce = {
                            #     'SIB': {
                            #         'TAC': self._tac,
                            #         'CellID': self._cid,
                            #         'PCI': self._pci,
                            #         'EARFCN': self._earfcn,
                            #         'geolocation': {
                            #             'lat': self._last_lat,
                            #             'lng': self._last_lng,
                            #         },
                            #         'mcc': self._mcc,
                            #         'mnc': self._mnc,
                            #     }
                            # }

                            # produce_json(to_produce, json_final)

                        elif first == 'QCLTE_PNCELL':

                            if (l_len - 2) % 13 != 0:
                                syntax_error(self._line_num, 'Line has an invalid length : {}'.format(l_len))

                            if (l_len - 2) % 13 != 0:
                                syntax_error(self._line_num, "Invalid PNCELL line.")

                            for i in range(2, l_len):

                                i2 = i - 2
                                curr_cell = line[i]

                                if not curr_cell == '':
                                    if i2 % 13 == 0:  # PCI
                                        curr_pci = int(curr_cell)
                                        self._pcis.append(curr_pci)
                                    elif i2 % 13 == 1:
                                        curr_earfcn = int(curr_cell)
                                        self._earfcns.append(curr_earfcn)

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

            # Producing EARFCN / PCI fields
            ep_fields = list(zip(self._earfcns, self._pcis))
            ep_fields.sort()
            self._data_dict.update({ep: [] for ep in ep_fields})

    def second_read(self):

        # Re-opening AOF file
        with open(self._path) as aof:

            # Goto content start.
            # The file structure had been checked a first time, so we don't need of the Description part.
            for i in range(self._content_start):
                aof.readline()

            line = read_line(aof)

            last_meas_index = -1
            last_meas_tstamp = -1

            index = 0

            last_gps_ind = -1
            last_pos = (0.0, 0.0)

            while line[0] != '':

                l_len = len(line)
                first = line[0]

                tstamp = 0

                if first != '<Content End>\n':

                    if l_len < 2:
                        syntax_error(self._line_num, "2 columns minimum expected, {} found.".format(l_len))

                    tstamp = get_tstamp(line[1])

                if first == 'QCLTE_PSCELL':

                    serving_earfcn = int(line[2])
                    serving_pci = int(line[4])
                    serving_rsrp = float(line[5])
                    serving_rsrq = float(line[10])
                    serving_rssi = float(line[15])

                    serving_cinr = 0.0  # TODO CINR

                    insert_data(self._data_dict, {
                        'name': ['MEASURE_SERVING'], 'timestamp': [tstamp], 'lat': [None], 'lng': [None],
                        'earfcn': [serving_earfcn], 'pci': [serving_pci]
                    }, 1)

                    to_insert = {
                        'name': ['MEASUREMENT'] * 4, 'timestamp': [tstamp] * 4, 'lat': [None] * 4, 'lng': [None] * 4,
                        'meas_name': ['RSRP', 'RSRQ', 'RSSI', 'CINR'],
                        (serving_earfcn, serving_pci): [serving_rsrp, serving_rsrq, serving_rssi, serving_cinr],
                    }

                    if last_meas_tstamp == tstamp:
                        replace_data(self._data_dict, to_insert, last_meas_index, 4)
                    else:
                        insert_data(self._data_dict, to_insert, 4)
                        last_meas_index = index
                        index += 4
                        last_meas_tstamp = tstamp

                elif first == 'QCLTE_PNCELL':

                    if (l_len - 2) % 13 != 0:
                        syntax_error(self._line_num, "Invalid PNCELL line.")

                    curr_earfcn = 0
                    curr_pci = 0
                    curr_rsrp = None
                    curr_rsrq = None

                    to_insert = {
                        'name': ['MEASUREMENT'] * 4, 'timestamp': [tstamp] * 4, 'lat': [None] * 4, 'lng': [None] * 4,
                        'meas_name': ['RSRP', 'RSRQ', 'RSSI', 'CINR']
                    }

                    for i in range(2, l_len):

                        i2 = i - 2
                        curr_cell = line[i]

                        if curr_cell != '':

                            if i2 % 13 == 0:  # PCI

                                curr_pci = int(curr_cell)

                            elif i2 % 13 == 1:

                                curr_earfcn = int(curr_cell)

                            elif i2 % 13 == 2:

                                curr_rsrp = float(curr_cell)

                            elif i2 % 13 == 5:

                                curr_rsrq = float(curr_cell)

                            elif i2 % 13 == 8:

                                curr_rssi = float(curr_cell)
                                curr_cinr = 0.0  # TODO Calculate CINR

                                to_insert[(curr_earfcn, curr_pci)] = [curr_rsrp, curr_rsrq, curr_rssi, curr_cinr]

                    if last_meas_tstamp == tstamp:
                        replace_data(self._data_dict, to_insert, last_meas_index, 4)
                    else:
                        insert_data(self._data_dict, to_insert, 4)
                        last_meas_index = index
                        index += 4
                        last_meas_tstamp = tstamp

                elif first == 'GPS':

                    curr_pos = (float(line[3]), float(line[2]))

                    last_tstamp = 0.0

                    if last_gps_ind == -1:
                        last_pos = curr_pos
                        last_tstamp = tstamp
                    else:
                        last_tstamp = self._data_dict['timestamp'][last_gps_ind]

                    estimator = generate_estimator(last_pos, curr_pos, last_tstamp, tstamp)

                    for i in range(last_gps_ind + 1, index):
                        pos = estimator(self._data_dict['timestamp'][i])
                        self._data_dict['lat'][i] = pos[0]
                        self._data_dict['lng'][i] = pos[1]

                    last_gps_ind = index - 1
                    last_pos = curr_pos

                elif first == 'QCLTE_CELLINFO':

                    insert_data(self._data_dict, {
                        'name': ['CELLINFO'], 'timestamp': [tstamp], 'lat': [None], 'lng': [None],
                        'earfcn': [line[3]], 'pci': [line[2]], 'tac': [line[12]], 'cid': [line[9]],
                        'mcc': [line[14]], 'mnc': [line[15]]
                    }, 1)

                    index += 1

                line = read_line(aof)

        print('ok0')
        p = pd.DataFrame(self._data_dict)
        print('ok')

    def process_data(self):

        # Processing data

        # Ordering measurements columns by EARFCN / PCI

        df_meas = pd.DataFrame(self._final_meas_frame)

        # Classifiying measurements by EARFCN / PCI
        gr_meas = df_meas.groupby(['earfcn', 'pci'])

        # Storing EARFCNSs/ PCIs in a list.
        for group in gr_meas.groups.keys():
            self._earfcns.append(group[0])
            self._pcis.append(group[1])

        # Creating final measurements dataframe.
        # final_meas = pd.DataFrame(columns=['id', 'name', 'timestamp', 'lat', 'lng'] + self._earfcns)

        # Final measurement dictionnary.
        meas_dict = {'id': [], 'name': [], 'timestamp': [], 'lat': [], 'lng': [], 'meas_name': []}

        # Generating EARFCNs / PCIs
        ep_list = list(zip(self._earfcns, self._pcis))
        ep_list.sort()
        meas_dict.update({ep: [] for ep in ep_list})

        # Grouping measurements by IDs, produce data from these groups.
        gr_meas = df_meas.groupby(['id'])

        for gr_id in gr_meas.groups.keys():

            gr_data = gr_meas.get_group(gr_id)

            gr_name = gr_data.groupby(['meas_name'])

            for gn_name in gr_name.groups:

                gn_data = gr_name.get_group(gn_name)

                first_entry = gn_data.iloc[0]

                data_dict = {
                    'id': gr_id, 'name': 'MEASUREMENT', 'timestamp': first_entry['timestamp'],
                    'lat': first_entry['lat'], 'lng': first_entry['lng'], 'meas_name': gn_name
                }
                data_dict.update({ep: None for ep in ep_list})

                for g in gn_data.iloc:
                    data_dict[(g['earfcn'], g['pci'])] = g['value']

                append_dict(meas_dict, data_dict)

        final_meas_dataframe = pd.DataFrame(meas_dict)

        return pd.concat([
            pd.DataFrame(final_meas_dataframe),
            pd.DataFrame(self._final_cinfo_frame),
            pd.DataFrame(self._final_serv_frame)
        ])

    def produce_pcaps(self):
        """Produce PCAP files for each dissector from produced TXT files using text2pcap.

        Raises:
            CalledProcessError: if text2pcap produces an error.
        """
        # Controlling fkey.
        # if fkey not in self.DICT_FILES_NAMES.keys():
        #    raise RuntimeError('Error : invalid file key : {}.'.format(fkey))

        for fkey in self.DICT_FILES_NAMES.keys():
            input_txt = getPathText(self.get_file_name(fkey, 'txt'))
            output_pcap = getPathText(self.get_file_name(fkey, 'pcap'))

            pcaputils.produce_pcap(input_txt, output_pcap, _DICT_DISSECTOR[fkey])

    def merge_pcaps(self):
        """Merges temporary PCAP files into the file 'final_tmp.pcap'.

        Raises:
            CalledProcessError: if mergecap produces an error.
        """

        pcaps_list = [self.get_file_name(fkey, 'pcap') for fkey in self.DICT_FILES_NAMES.keys()]

        pcaputils.merge_pcaps(pcaps_list, 'final_tmp.pcap')

    @staticmethod
    def reorder_pcap():
        """Reorders the file 'final_tmp.pcap'. If a reordering has been done, produces the file
        'ord_final_tmp.pcap'.

        Raises:
            CalledProcessError: if reordercap produces an error.
        """
        pcaputils.reorder_pcap('final_tmp.pcap', 'ord_final_tmp.pcap')

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

    def finalize(self, outdir: str):
        """Produces the final files in the output directory.

        The produced files are MCC_MNC_ID.pcap, which contains all messages packets,
        and CMCC_MNC_FNAME_ID.json, which contains all measurement and SIB information
        used for the Cell Association Processing; here, MCC and MNC designate the MCC/MNC
        of the current operator, ID the identifier used to designate the phone, and FNAME the
        AOF file name parsed.

        Parameters:
            outdir: output directory.
        """

        # Producing final PCAP file.
        output_pcap = '{0}_{1}_{2}.pcap'.format(self.mcc, self.mnc, self.phone_id)

        # Choosing between ordered file if exists or non ordered file.
        input_pcap = 'ord_final_tmp.pcap' if os.path.exists(getPathText('ord_final_tmp.pcap')) else 'final_tmp.pcap'

        shutil.copy2(getPathText(input_pcap), os.path.join(outdir, output_pcap))

        # Producing final JSON file.
        output_json = 'C{0}_{1}_{2}_{3}.json'.format(self.mcc, self.mnc, getfileName(self._path), self.phone_id)
        shutil.copy2(getPathText('json_tmp.json'), os.path.join(outdir, output_json))

    def _get_phone_id(self) -> str:
        """
            Getter of the phone_id attribute associated to the AOF file.

            Returns:
                the phone ID attribute
        """
        return self._phone_id

    def _get_mcc(self) -> int:
        return self._mcc

    def _get_mnc(self) -> int:
        return self._mnc

    # Class properties.
    phone_id = property(_get_phone_id)
    mcc = property(_get_mcc)
    mnc = property(_get_mnc)
