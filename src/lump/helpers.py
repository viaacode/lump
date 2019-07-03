# Some code copied from ebu/benchmarkstt (by original author), see
# https://github.com/ebu/benchmarkstt/blob/master/LICENCE.md

from functools import partial, wraps


class DeferredCallback:
    """Simple helper class to defer the execution of formatting functions until it is needed"""

    def __init__(self, cb, *args, **kwargs):
        self._cb = wraps(cb)(partial(cb, *args, **kwargs))

    def __str__(self):
        return self._cb()

    def __repr__(self):
        return '<%s:%s>' % (self.__class__.__name__, repr(self._cb()))


class DeferredList:
    def __init__(self, cb):
        self._cb = cb
        self._list = None

    @property
    def list(self):
        if self._list is None:
            self._list = self._cb()
        return self._list

    def __getitem__(self, item):
        return self.list[item]


def make_printable(char):
    """
    Return printable representation of ascii/utf-8 control characters

    :param str char:
    :return str:
    """
    if not len(char):
        return ''
    if len(char) > 1:
        return ''.join(list(map(make_printable, char)))

    codepoint = ord(char)
    if 0x00 <= codepoint <= 0x1f or 0x7f <= codepoint <= 0x9f:
        return chr(0x2400 | codepoint)

    return char if char != ' ' else '·'
