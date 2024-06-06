def prefix_with_zeros(left_digits: int, nb: str, sep: str = ".") -> str:
    """Prefixes nb with 0 until it has `left_digits` amount of digits in the left part
    :param left_digits: Amount of digits nb is supposed to have on the left part
    :param nb: floating number as string where left and right parts are separated by `sep`
    :param sep: separator of the number
    :return: given number prefixed with 0 to have `left_digits` digits in the left part
    """
    parts = nb.split(sep)
    left = parts[0]
    right = parts[1]
    if len(left) < left_digits:
        for i in range(left_digits - len(left)):
            left = "0" + left
    return left + sep + right
