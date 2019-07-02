from functools import partial

_prefixes = 'kMGTPEZY'


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
        prefixes = _prefixes

    if precision is None:
        precision = 2

    format_string = '%%.%df%%s%%s%%s' % (precision,)

    if abs(num) < base:
        return format_string % (num, '', '', suffix)

    prev_unit = ''

    for unit in prefixes:
        if abs(num) < base:
            return format_string % (num, prev_unit, midfix, suffix)
        num /= base
        prev_unit = unit
    return format_string % (num, unit, midfix, suffix)


format_binary = partial(format_metric, midfix='i', base=1024, prefixes=_prefixes.upper())
