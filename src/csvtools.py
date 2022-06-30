"""This module provides classes to handle CSV file format used by the program."""

import re

# Constants
# Regular expressions.
REGEX_KEYS_NAMES = r'\w+'
REGEX_VALUES = r'([^\s|]| )*'


class CSVWriter:
    """This class handles the writing of CSV-derivative files used in this program.

    This class supports context managers, and can be used in a with ... as statement.
    """

    def __init__(self, fname: str, header: dict):
        """Class constructor.

        Parameters:
            fname: name of the file to write in.
            header: dictionary which represents the DEFINE part of the file, with dictionary string keys as entries
            identifiers and dictionary string list values as values of the entry.
        """

        # Controlling types.

        if type(fname) != str:
            raise TypeError('Invalid filename type, str type expected.')

        if type(header) != dict:
            raise TypeError('Invalid header type, dict type expected.')

        self._fname = fname

        self._file = None

        # Testing header validity.

        for k in header.keys():

            # Checking key type.
            ktype = type(k)
            if ktype != str:
                raise TypeError("error : str type expected for key, {} found.".format(ktype))

            # Checking key syntax.
            if not re.fullmatch(REGEX_KEYS_NAMES, str(k)):
                raise RuntimeError("error : invalid key syntax : '{}'".format(k))

            row = header[k]

            # Checking row type.
            trow = type(row)
            if trow != list:
                raise TypeError('error : list type expected for file header, {} type found'.format(trow))

            if len(row) == 0:
                raise RuntimeError('error : field name list should contain at least one element.')

            for r in row:
                # Checking column name types.
                rtype = type(r)
                if rtype != str:
                    raise TypeError('error : str type expected for field names, {} type found'.format(rtype))

                # Checking column names syntax.
                if not re.fullmatch(REGEX_KEYS_NAMES, r):
                    raise RuntimeError("error : invalid column name syntax : '{}'".format(r))

        self._header = header

    def open_file(self):
        """Opens the CSV file to write in.
        If the CSV file doesn't exist, it will be created.
        """
        self._file = open(self._fname, 'w')

        self._file.write('DEFINE\n')

        # Writing DEFINE part

        for k in self._header.keys():
            self._file.write(k)

            names = self._header[k]

            for name in names:
                self._file.write('|')
                self._file.write(name)

            self._file.write('\n')

        self._file.write('CONTENT\n')

    def close_file(self):
        """Closes the CSV file."""
        self._file.close()

    def write_row(self, row: list):
        """Writes a row in the CONTENT part of the CSV file.

        Parameters:
            row: row to be written in the CSV file, as a list. The first element of this list must correspond to one of
            the keys present in the header (DEFINE part). The following values must be strings, and must not contain
            any spacing character other than space nor any vertical '|' character.
        """
        rlen = len(row)

        # Checking row size.
        if rlen < 2:
            raise RuntimeError("error : row of length greater than or equal to 2 expected, {} rows found.".format(rlen))

        field_type = row[0]

        # Checking syntax of the field type.
        if not re.fullmatch(REGEX_KEYS_NAMES, field_type):
            raise RuntimeError("error : invalid field type syntax : {} ".format(field_type))

        # Checking existence of the message type.
        if field_type not in self._header.keys():
            raise KeyError("error : unknown field type : {}".format(field_type))

        # Writing the row.
        for i in range(rlen):

            s = str(row[i]) if row[i] is not None else ''

            # Checking value syntax.
            if not re.fullmatch(REGEX_VALUES, s):
                raise RuntimeError("error : invalid value syntax : {}".format(field_type))

            self._file.write(s)

            # Inserting separator
            if rlen != i + 1:
                self._file.write('|')

        self._file.write('\n')

    # Getters

    def _get_filename(self):
        """Returns:
            The name of the file to be written.
        """
        return self._fname

    def _get_header(self):
        """Returns :
        A copy of the header dictionary.
        """
        return dict(self._header)

    # With ... as ... handling

    def __enter__(self):
        self.open_file()
        return self

    def __exit__(self, typ, val, trace):
        if self._file:
            self.close_file()

    filename = property(_get_filename)
    header = property(_get_header)


class CSVReader:

    def __init__(self, fname):
        self._fname = fname
        self._file = None
        self._header = {}

    def open_file(self):

        with open(self._fname) as file:
            state = 0

            line = file.readline().split('|')
            llen = len(line)

            if llen == 0:
                raise RuntimeError('error : empty file.')

            line_num = 1
            first = line[0]
            entry_counter = 0

            while first != '':

                if state == 0:

                    if first == 'DEFINE\n':
                        state = 1
                    else:
                        raise RuntimeError("error : file must begin with 'DEFINE'")

                elif state == 1:

                    if first == 'CONTENT\n':
                        if entry_counter == 0:
                            raise RuntimeError("error : no entry type defined.")
                        state = 2
                    else:

                        entry_counter += 1

                        key = ''

                        for i in range(llen):

                            cols = line[i].strip()

                            if i == 0:
                                if not re.fullmatch(REGEX_KEYS_NAMES, cols):
                                    raise RuntimeError(
                                        "error : line {0} : invalid key syntax : {1}".format(line_num, cols))
                                self._header[cols] = []
                                key = cols
                            else:
                                if not re.fullmatch(REGEX_KEYS_NAMES, cols):
                                    raise RuntimeError(
                                        "error : line {0} : invalid field syntax : {1}".format(line_num, cols))
                                self._header[key].append(cols)

                elif state == 2:

                    for i in range(llen):

                        cols = line[i].strip()

                        if i == 0:

                            if not re.fullmatch(REGEX_KEYS_NAMES, cols):
                                raise RuntimeError(
                                    "error : line {0} : invalid key syntax : {1}".format(line_num, cols))

                            if cols not in self._header.keys():
                                raise RuntimeError("error : invalid key : {}".format(cols))

                        else:

                            if not re.fullmatch(REGEX_VALUES, cols):
                                raise RuntimeError(
                                    'error : line {0} : invalid value syntax : {1}'.format(line_num, cols))

                line_num += 1
                line = file.readline().split('|')
                llen = len(line)
                first = line[0]

        self._file = open(self._fname)

        first = self._file.readline().split('|')[0]
        while first != 'CONTENT\n':
            first = self._file.readline().split('|')[0]

    def read_line(self) -> list:
        return [col.strip() for col in self._file.readline().split('|')]

    def get_header(self) -> dict:
        return dict(self._header)

    def close_file(self):
        self._file.close()

    def __enter__(self):
        self.open_file()
        return self

    def __exit__(self, typ, val, trace):
        if self._file:
            self.close_file()
