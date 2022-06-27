def insert_data(d1: dict, d2: dict, length: int):
    """Insert data of a dictionary d2 in another dictionary d1.

    Fields present in d1 but not in d2 will be completed with length None values.

    Parameters:
        d1: dictionary where the data will be inserted.
        d2: dictionnary which contains data to be inserted.
        length: length of data set to be inserted.
    """
    for k in d1.keys():
        d1[k].extend([None] * length if k not in d2.keys() else d2[k])


def fill_data(d1: dict, d2: dict, index: int, length: int):
    """Fills rows from a dictionary d1 with rows in a dictionary d2 over length.

    Values already present in d1 will not be replaced.

    Parameters:
        d1: dictionary to fill.
        d2: dictionnary which contains data to be written in d1.
        index: start index of the part to be filled in d1.
        length: length of the part to be filled in d1.
    """
    for k in d1.keys():
        if k in d2.keys():
            for i in range(index, index + length + 1):
                if d1[k][i] is None:
                    d1[k][i] = d2[k][i - index]