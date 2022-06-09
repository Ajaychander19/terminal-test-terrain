"""This module provides classes to handle CSV file format used by the program."""

import re

class CSVReader:
    pass

class CSVWriter:
    def __init__(self, fname: str, header: dict):
        self._fname = fname

        self._file = None

        for k in header.keys():

            # Checking key type.
            ktype = type(k)
            if ktype != str:
                raise TypeError("error : str type expected for key, {} found.".format(ktype))

            # Checking key syntax.
            if not re.fullmatch(r'\w+', str(k)):
                raise RuntimeError("error : invalid key syntax : {} ".format(k))

            row = header[k]

            # Checking row type.
            trow = type(row)
            if trow != list:
                raise TypeError('error : list type expected for file header, {} type found'.format(trow))

            for r in row:
                # Checking column name types.
                rtype = type(r)
                if r != str:
                    raise TypeError('error : str typr expected for field names, {} type found'.format(trow))

                # Checking column names syntax.
                if not re.fullmatch(r'\w*', r):
                    raise RuntimeError("error : invalid column name syntax : {} ".format(k))

        self._header = header

    def open_file(self):
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
        self._file.close()

    def write_row(self, row: list):

        rlen = len(row)

        # Checking row size.
        if rlen < 2:
            raise RuntimeError("error : row of length greater than or equal to 2 expected, {} rows found.".format(rlen))

        field_type = row[0]

        # Checking syntax of the field type.
        if not re.fullmatch(r'\w+', field_type):
            raise RuntimeError("error : invalid field type syntax : {} ".format(field_type))

        # Checking existence of the message type.
        if field_type not in self._header.keys():
            raise RuntimeError("error : unknown field type : {}".format(field_type))

        # Writing the row.
        for i in range(rlen):

            s = str(row[i])

            # Checking value syntax.
            if not re.fullmatch(r'(\w|\.)*', s):
                raise RuntimeError("error : invalid value syntax : {}".format(field_type))

            self._file.write(s)

            # Inserting separator
            if rlen != i + 1:
                self._file.write('|')

        self._file.write('\n')

    # Getters

    def _get_filename(self):
        return self._fname

    def _get_header(self):
        pass

    # With ... as ... handling

    def __enter__(self):
        self.open_file()
        return self

    def __exit__(self):
        if self._file:
            self.close_file()

    filename = property(_get_filename)
    header = property(_get_header)
