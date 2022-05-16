"""This module is dedicated to the analysis of AOF files produced by Accuver Xcal."""

# Constants
_DICT_DISSECTOR = {
    'BCCH:DL_SCH': 149,
    'PCCH': 150,
    'DL DCCH': 153,
    'UL DCCH': 154
    # TODO Other channel types.
}


def get_dissector_num(diss_name: str):
    return _DICT_DISSECTOR[diss_name]


def write_txt_from_msg_list(path: str, msgs: list):
    with open(path, 'a') as out:
        for msg in msgs:
            out.write('{0}\n0000 {1}\n\n'.format(msg.date, msg.data))

def read_line(f):
    return f.readline().split('|')

def syntax_error(line: int, msg: str):
    raise RuntimeError('Error: line {0}, {1}'.format(line, msg))

class XcalMessage:

    def __init__(self, date: str, data: str):
        self._date = date
        self._data = data

    def _get_date(self):
        return self._date

    def _get_data(self):
        return self._data

    date = property(_get_date)
    data = property(_get_data)


class XcalConverter:

    def __init__(self):
        self._txt_data = {
            'BCCH:DL_SCH': [],
            'PCCH': [],
            'DL DCCH': [],
            'UL DCCH': [],
        }
        self._gps = []

    def parse_aof(self, path: str):

        state = 0  # Current automata state.
        line_num = 1  # Line number.

        # Opening AOF file.
        with open(path, 'r') as aof:

            line = read_line(aof)  # Current line.

            # Parsing automata
            while len(line) != 0 and state != 6:

                # First word of the line.
                first = line[0]

                if state == 0:  # Initial state.

                    if first == '<AOF_Information_START>':
                        state = 1
                    else:
                        syntax_error(line_num, 'Invalid file starting "{}"'.format(first))

                elif state == 1:    # Skipping AOF info section.

                    if first == '<AOF_Information_END>':
                        state = 2

                elif state == 2:    # Description section start.

                    if first == '<Description Start>':
                        state = 3
                    else:
                        syntax_error(line_num, 'Invalid description start "{}"'.format(first))

                elif state == 3:    # Description section skip.

                    if first == '<Description End>':
                        state = 4

                elif state == 4:    # Content section start.

                    if first == '<Content Start>':
                        state = 5
                    else:
                        syntax_error(line_num, 'Invalid content start "{}"'.format(first))
                        
                elif state == 5:    # Content parsing.

                    if first == 'QCLTE_RRCMSG_V2':
                        pass    # TODO Parse LTE Message
                    elif first == 'GPS':
                        pass    # TODO Parse GPS message
                    elif first == 'QCLTE_PSCELL':
                        pass    # TODO Parse PSCELL
                    elif first == '<Content End>':  # File ending.
                        state = 6

                line = read_line(aof)   # Next line.
                line_num += 1
                    
        # Check if we are in the final state after finishing the parsing.
        if state != 6:
            syntax_error(line_num, 'Unexpected End Of File.')
