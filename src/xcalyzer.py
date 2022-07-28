"""This module is dedicated to the analysis of AOF files produced by Accuver Xcal."""

from constantPath import getPathText, getfileName
from dictutils import insert_data, fill_data

import datetime
import os
import shutil

import pcaputils
import csvtools

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
        # self._gps = []

        self._path = path
        self._phone_id = 'phone_1'  # FIXME Temporary ID

        self._earfcns = []
        self._pcis = []

        self._data_dict = {
            'name': [], 'timestamp': [], 'lat': [], 'lng': [],                          # Common fields
            'earfcn': [], 'pci': [],  'rsrp': [], 'rsrq': [], 'rssi': [], 'cinr': [],   # Serving Cell
            'tac': [], 'cid': [], 'mcc': [], 'mnc': [],                                 # Cell information
            'meas_name': []                                                             # Measurement
        }

        self._mcc = None
        self._mnc = None

        self._content_start = 0

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
        """Processes the AOF file.

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

        The first output CSV file is also produced by this function ; firstly, the AOF file syntax is checked.
        The lengths of messages and the structure of the different sections of the file are checked. EARFCN / PCIs
        couples are also referenced during this step. Then, during the second step, the file is re-read, and all
        data inside it are processed, to make the EARFCNs and PCIs / Measurements tables.

        The output file produced is written in CSV, with a syntax based on the AOF format.

        Raises:
            RuntimeError: if an error occurred during the analysis of the AOF file.
        """

        print('Parsing AOF file...')
        self.first_read()
        print('AOF file parsing done.')

        print('Data processing...')
        self.second_read()
        print('Data processing done.')

        print('Producing CSV file...')
        self.produce_csv_file()
        print('CSV file produced.')

    def first_read(self):
        """Does the first reading of the AOF file.

        This function checks:
            - The presence of each section of the file.
            - The structure of messages (especially messages length).

        This function also scans all EARFCNs/PCIs couples present in the file.

        Raises:
            RuntimeError: if the syntax of the file is invalid.
        """

        line_num = 0    # Number of the line which is parsed.

        # Opening AOF file.
        with open(self._path, 'r') as aof:

            try:

                line = read_line(aof)  # Current line.

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
                            syntax_error(line_num, 'Invalid file starting "{}"'.format(first))

                    elif state == 1:  # Skipping AOF info section.

                        if first == '<AOF_Information_END>\n':
                            state = 2

                    elif state == 2:  # Description section start.

                        if first == '<Description Start>\n':
                            state = 3
                        else:
                            syntax_error(line_num, 'Invalid description start "{}"'.format(first))

                    elif state == 3:  # Description section skip.

                        if first == '<Description End>\n':
                            state = 4

                    elif state == 4:  # Content section start.

                        if first == '<Content Start>\n':
                            state = 5
                            self._content_start = line_num
                        else:
                            syntax_error(line_num, 'Invalid content start "{}"'.format(first))

                    elif state == 5:  # Getting phone ID, opening temporary files.

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

                        if first != '<Content End>\n':

                            if l_len < 2:
                                syntax_error(line_num, "2 columns minimum expected, {} found.".format(l_len))

                        if first == 'QCLTE_RRCMSG_V2' or first == 'QCLTE_RRCMSG':

                            is_v2 = first == 'QCLTE_RRCMSG_V2'

                            # Check if the line has a valid length.
                            if l_len < 13:
                                syntax_error(line_num, "13 columns expected, {} found.".format(l_len))

                            msg_type = line[6 if is_v2 else 5]  # Message type.
                            payload = line[12 if is_v2 else 11]  # Message payload.

                            # Check if the message type is valid.
                            if msg_type not in self._files.keys():
                                syntax_error(line_num, "Invalid message type : {}".format(msg_type))

                            # Adding the message to the corresponding file.
                            self._files[msg_type].write(
                                '{0}\n0000 {1}\n'.format(line[1], payload))

                        elif first == 'GPS':

                            if l_len < 9:
                                syntax_error(line_num, '8 columns expected, {} found.'.format(l_len))

                        elif first == 'QCLTE_PSCELL':

                            if l_len < 21:
                                syntax_error(line_num, "16 columns expected, {} found.".format(l_len))

                            # Store serving EARFCN/PCI couple for the step two.
                            serving_earfcn = int(line[2])
                            serving_pci = int(line[4])

                            if (serving_earfcn, serving_pci) not in zip(self._earfcns, self._pcis):
                                self._earfcns.append(serving_earfcn)
                                self._pcis.append(serving_pci)

                        elif first == 'QCLTE_CELLINFO':

                            if l_len < 16:
                                syntax_error(line_num, "16 columns expected, {} found.".format(l_len))

                            # Storing MCC / MNC to use them to produce the name of the output CSV file.
                            if self._mcc is None:
                                self._mcc = line[14]
                                self._mnc = line[15]

                        elif first == 'QCLTE_PNCELL':

                            if (l_len - 2) % 13 != 0:
                                syntax_error(line_num, "Invalid PNCELL line.")

                            # Storing neighbours EARFCN/PCI couples for the step two.

                            curr_pci = 0

                            # Reading the whole line to find EARFCNs and PCIs...
                            for i in range(2, l_len):

                                i2 = i - 2
                                curr_cell = line[i]

                                # Avoid empty cells at the end of the line.
                                if not curr_cell == '':

                                    if i2 % 13 == 0:    # PCI
                                        curr_pci = int(curr_cell)
                                    elif i2 % 13 == 1:  # EARFCN
                                        curr_earfcn = int(curr_cell)

                                        # Storing EARFCNs and PCIs
                                        if (curr_earfcn, curr_pci) not in list(zip(self._earfcns, self._pcis)):
                                            self._earfcns.append(curr_earfcn)
                                            self._pcis.append(curr_pci)

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

            # Producing EARFCN / PCI fields
            ep_fields = list(zip(self._earfcns, self._pcis))
            ep_fields.sort()
            self._data_dict.update({ep: [] for ep in ep_fields})

    def second_read(self):
        """Reads a second time the AOF file and processes its data.

        This function make the EARFCNs/PCIs correspondance with measurements, and also
        includes cell information and serving cell messages.

        Geolocations are calculated for each produced message between two GPS measurement using a linear estimator.
        """

        # Re-opening AOF file
        with open(self._path) as aof:

            # Goto content start.
            # The file structure had been checked a first time, so we don't need of the Description part.
            for i in range(self._content_start + 1):
                aof.readline()

            line = read_line(aof)

            last_meas_index = -1        # Index of the last measurement.
            last_meas_tstamp = -1       # Timestamp of the last measurement.

            index = 0   # Current index;

            last_gps_ind = -1       # Index of the last GPS estimation group.
            last_pos = (0.0, 0.0)

            # Reading the file line per line...
            while line[0] != '':

                l_len = len(line)
                first = line[0]

                tstamp = 0

                if first != '<Content End>\n':

                    tstamp = get_tstamp(line[1])

                if first == 'QCLTE_PSCELL':

                    # Reading data for serving cell.
                    serving_earfcn = int(line[2])
                    serving_pci = int(line[4])
                    serving_rsrp = float(line[5])
                    serving_rsrq = float(line[10])
                    serving_rssi = float(line[15])
                    serving_cinr = float(line[20])

                    # Inserting serving ERAFCN / PCI.
                    insert_data(self._data_dict, {
                        'name': ['MEASURE_SERVING'], 'timestamp': [tstamp], 'lat': [None], 'lng': [None],
                        'earfcn': [serving_earfcn], 'pci': [serving_pci], 'rsrp': [serving_rsrp],
                        'rsrq': [serving_rsrq], 'rssi': [serving_rssi], 'cinr': [serving_cinr]
                    }, 1)

                    index += 1

                    # Inserting measurement data.
                    to_insert = {
                        'name': ['MEASUREMENT'] * 3, 'timestamp': [tstamp] * 3, 'lat': [None] * 3, 'lng': [None] * 3,
                        'meas_name': ['RSRP', 'RSRQ', 'RSSI'],
                        (serving_earfcn, serving_pci): [serving_rsrp, serving_rsrq, serving_rssi],
                    }

                    if last_meas_tstamp == tstamp:

                        # If a measurement with the same timestamp exists, completing this measurement.
                        fill_data(self._data_dict, to_insert, last_meas_index, 3)

                    else:

                        # Inserting a new measurement.
                        insert_data(self._data_dict, to_insert, 3)
                        last_meas_index = index
                        index += 3
                        last_meas_tstamp = tstamp

                elif first == 'QCLTE_PNCELL':

                    # Multiple measurements.
                    curr_earfcn = 0
                    curr_pci = 0
                    curr_rsrp = None
                    curr_rsrq = None
                    curr_rssi = None

                    to_insert = {
                        'name': ['MEASUREMENT'] * 3, 'timestamp': [tstamp] * 3, 'lat': [None] * 3, 'lng': [None] * 3,
                        'meas_name': ['RSRP', 'RSRQ', 'RSSI']
                    }

                    # Reading measurements...
                    for i in range(2, l_len):

                        i2 = i - 2
                        curr_cell = line[i]

                        if curr_cell != '':

                            if i2 % 13 == 0:    # PCI

                                curr_pci = int(curr_cell)

                            elif i2 % 13 == 1:  # EARFCN

                                curr_earfcn = int(curr_cell)

                            elif i2 % 13 == 2:  # RSRP

                                curr_rsrp = float(curr_cell)

                            elif i2 % 13 == 5:  # RSRQ

                                curr_rsrq = float(curr_cell)

                            elif i2 % 13 == 8:  # RSSI

                                curr_rssi = float(curr_cell)

                                to_insert[(curr_earfcn, curr_pci)] = [curr_rsrp, curr_rsrq, curr_rssi]

                    if last_meas_tstamp == tstamp:

                        # If a measurement with the same timestamp exists, completing this measurement.

                        fill_data(self._data_dict, to_insert, last_meas_index, 3)

                    else:

                        # Inserting a new measurement.
                        insert_data(self._data_dict, to_insert, 3)
                        last_meas_index = index
                        index += 3
                        last_meas_tstamp = tstamp

                elif first == 'QCLTE_CELLINFO':

                    insert_data(self._data_dict, {
                        'name': ['CELLINFO'], 'timestamp': [tstamp], 'lat': [None], 'lng': [None],
                        'earfcn': [line[3]], 'pci': [line[2]], 'tac': [line[12]], 'cid': [line[9]],
                        'mcc': [line[14]], 'mnc': [line[15]]
                    }, 1)

                    index += 1

                new_line = read_line(aof)

                if first == 'GPS' or new_line == ['']:

                    # Current geolocation.
                    if first == 'GPS':
                        curr_pos = (float(line[3]), float(line[2]))

                        # If the GPS message is the first, completing the last geolocation with it.
                        if last_gps_ind == -1:
                            last_pos = curr_pos
                            last_tstamp = tstamp
                        else:
                            last_tstamp = self._data_dict['timestamp'][last_gps_ind]

                    estimator = generate_estimator(last_pos, curr_pos, last_tstamp, tstamp)

                    # Applying the estimator on the geolocation group.
                    for i in range(last_gps_ind + 1, index):
                        pos = estimator(self._data_dict['timestamp'][i])
                        self._data_dict['lat'][i] = pos[0]
                        self._data_dict['lng'][i] = pos[1]

                    last_gps_ind = index - 1
                    last_pos = curr_pos

                line = new_line

    def produce_csv_file(self):
        """Produces the CSV output file following the previous data processing."""

        csv_header = {
            'MEAS_EARFCNS': ['NA', 'NA', 'NA', 'NA', 'EARFCN1', 'EARFCN2', 'EARFCN3', 'etc'],
            'MEAS_PCIS': ['NA', 'NA', 'NA', 'NA', 'PCI1', 'PCI2', 'PCI3', 'etc'],
            'CELLINFO': ['Timestamp', 'Lat', 'Lng', 'EARFCN', 'PCI', 'TAC', 'CID', 'MCC', 'MNC'],
            'MEASURE_SERVING': [
                'Timestamp', 'Lat', 'Lng', 'Serving_EARFCN', 'Serving_PCI',
                'Serving_RSRP', 'Serving_RSRQ', 'Serving_RSSI', 'Serving_CINR'
            ],
            'MEASUREMENT': ['Timestamp', 'Lat', 'Lng', 'Measurement_Name', 'Values']
        }

        # First timestamp.
        tstamp_zero = self._data_dict['timestamp'][0]

        with csvtools.CSVWriter(getPathText('csv_tmp.csv'), csv_header) as csv_out:

            # Lists of EARFCN/PCI couples.
            ep_list = list(zip(self._earfcns, self._pcis))
            ep_list.sort()

            # Writing couples in the file.
            csv_out.write_row(['MEAS_EARFCNS'] + [''] * 4 + [ep[0] for ep in ep_list])
            csv_out.write_row(['MEAS_PCIS'] + [''] * 4 + [ep[1] for ep in ep_list])

            # Writing data in the CSV file.
            for i in range(len(self._data_dict['name'])):

                # Common fields.
                name = self._data_dict['name'][i]
                to_write = [
                    name, self._data_dict['timestamp'][i] - tstamp_zero, self._data_dict['lat'][i],
                    self._data_dict['lng'][i]
                ]

                if name == 'CELLINFO':              # Cell information fields.
                    to_write.extend([
                        self._data_dict['earfcn'][i], self._data_dict['pci'][i], self._data_dict['tac'][i],
                        self._data_dict['cid'][i], self._data_dict['mcc'][i], self._data_dict['mnc'][i]
                    ])
                elif name == 'MEASURE_SERVING':     # Serving cell information fields.
                    to_write.extend([
                        self._data_dict['earfcn'][i], self._data_dict['pci'][i], self._data_dict['rsrp'][i],
                        self._data_dict['rsrq'][i], self._data_dict['rssi'][i], self._data_dict['cinr'][i]
                    ])
                elif name == 'MEASUREMENT':         # Measurement field.
                    to_write.append(self._data_dict['meas_name'][i])
                    to_write.extend([self._data_dict[ep][i] for ep in ep_list])

                csv_out.write_row(to_write)

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
        output_json = 'C{0}_{1}_{2}_{3}.csv'.format(self.mcc, self.mnc, getfileName(self._path), self.phone_id)
        shutil.copy2(getPathText('csv_tmp.csv'), os.path.join(outdir, output_json))

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
    """Raises a syntax error.

    Parameters:
        line: line of the file where the error occured.
        msg: error message.

    Raises:
        RuntimeError: the corresponding syntax error.
    """
    raise RuntimeError('Error: line {0}, {1}'.format(line, msg))


def get_tstamp(date: str) -> float:
    """Converts a POSIX date string to floating-point 64-bit timestamp.

    Parameters:
        date: POSIX formatted date string.

    Returns:
        The floating-point corresponding timestamp.
    """
    return datetime.datetime.fromisoformat(date).timestamp()


def generate_estimator(pos_a: (float, float), pos_b: (float, float), t1: float, t2: float):
    """Generates a linear geolocation estimator.

    Let pos_a and pos_b two geolocation measured at moments t_1 and t_2. The estimator is the
    linear function f which contains (t_1, pos_a) and (t_2, pos_b). Given a timestamp t, the
    corresponding geolocation found is f(t).

    The calculation is the following, given pos_a, pos_b the two geolocation and t the timestamp:
        f(t) = ((t - t1) / t2 - t1) * (pos_b - pos_a) + pos_a[0]
    considering pos_a and pos_b as two-dimensional vectors.

    If pos_a = pos_b, f(t) = t for all t.

    Parameters:
        pos_a: the starting position.
        pos_b: the ending position.
        t1: the starting timestamp.
        t2: the ending timestamp.

    Returns:
        The corresponding estimator function, which takes as parameter a timestamp float and returns a float couple
        which corresponds to the resulting position.
    """
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
