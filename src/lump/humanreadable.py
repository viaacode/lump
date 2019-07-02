def format_metric(num, suffix=None, base=None, midfix=None, prefixes=None, precision=None):
    """
    Format a number using prefixes according to base (by default using metric
    prefixes, and a suffix of 'B', representing the unit of digital information)
    :return: Formatted number
    :rtype: str
    """
    if suffix is None:
        suffix = 'B'

    if base is None:
        base = 1000

    if midfix is None:
        midfix = ''

    if prefixes is None:
        prefixes = 'KMGTPEZY'

    if precision is None:
        precision = 2

    format_string = '%%.%df' % (precision,)
    format_string += '%s%s%s'

    if abs(num) < base:
        return format_string % (num, '', midfix, suffix)

    num /= base

    for unit in prefixes:
        if abs(num) < base:
            return format_string % (num, unit, midfix, suffix)
        num /= base
    return format_string % (num, unit, midfix, suffix)
