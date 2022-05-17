"""This module is dedicated to the analysis of AOF files produced by Accuver Xcal."""

from constantPath import getPathText
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


def parse_aof(path: str):

    files = {
        'temporary': None,  # FIXME Unknown code for this protocol.
        'BCCH:DL_SCH': None,
        'PCCH': None,
        'DL CCCH': None,
        'DL DCCH': None,
        'UL CCCH': None,
        'UL DCCH': None,
    }

    dict_file_name = {
        'temporary': 'BCCH_BCH_148',   # FIXME Unknown code for this protocol.
        'BCCH:DL_SCH': 'BCCH_DL_149',
        'PCCH': 'PCCH_DL_150',
        'DL CCCH': 'CCCH_DL_151',
        'UL CCCH': 'CCCH_UL_152',
        'DL DCCH': 'DCCH_DL_153',
        'UL DCCH': 'DCCH_UL_154'
    }

    state = 0  # Current automata state.
    line_num = 1  # Line number.
    phone_id = 'phone_1'  # FIXME temporary id

    # Opening AOF file.
    with open(path, 'r') as aof:

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

                elif state == 3:  # Description section skip.

                    # if first == '<Description End>\n':
                    #    state = 4

                    # TODO Get phone ID.
                    if True:

                        # Opening files.
                        for k in files.keys():

                            path = getPathText(
                                '{0}_{1}.txt'.format(dict_file_name[k], phone_id)
                            )
                            files[k] = open(path, 'w')

                        state = 4

                elif state == 4:

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
                        msg_time = line[1]  # Message timestamp
                        msg_content = line[12]  # Message content.

                        # Check if the message type is valid.
                        if msg_type not in files.keys():
                            syntax_error(line_num, "Invalid message type : {}".format(msg_type))

                        # Adding the message to the corresponding list.
                        files[msg_type].write('{0}\n0000 {1}\n'.format(msg_time, msg_content))

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
            for k in files.keys():
                f = files[k]

                # Checking if the file is properly open...
                if f:
                    f.close()

    # Check if we are in the final state after finishing the parsing.
    if state != 7:
        syntax_error(line_num, 'Unexpected End Of File, state={}.'.format(state))

    return phone_id


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


# class XcalConverter:
#
#     def __init__(self):
#         # self._files = {
#         #     'BCCH:DL_SCH': None,
#         #     'PCCH': None,
#         #     'DL DCCH': None,
#         #     'UL DCCH': None,
#         # }
#         self._gps = []
#         self._phone_id = '1'        # _FIXME Temporary ID
#
#     def produce_dissect_file(self, dissect: str):
#         pass # _TODO Produce file for a particular dissector.
#
#     def _get_phone_id(self):
#         return self._phone_id
#
#     # Class properties.
#     phone_id = property(_get_phone_id)
