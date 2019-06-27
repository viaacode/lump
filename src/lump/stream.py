from io import RawIOBase


class IteratorStream(RawIOBase):
    """
    Access an iterator as a bytestream
    """

    def __init__(self, iterable, on_update=None):
        self._iterator = iterable
        self._on_update = on_update

    def read(self, size=None):
        try:
            res = next(self._iterator)
        except StopIteration:
            return
        if self._on_update:
            self._on_update()
        return res
