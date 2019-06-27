from tqdm import tqdm
import requests
from functools import partial
from lump.stream import IteratorToStream


class RequestIterator:
    """
    Iterates over `chunk_size` chunks of the contents of a file, provides a tqdm
    progress indicator.
    """

    def __init__(self, url, chunk_size=20480, **kwargs):
        file_size = int(requests.head(url).headers['Content-Length'])
        first_byte = 0

        header = {"Range": "bytes=%s-%s" % (first_byte, file_size)}
        self.pbar = tqdm(total=file_size, initial=first_byte,
                         unit='B', unit_scale=True, desc=url[-15:])

        self.req = requests.get(url, headers=header, stream=True, **kwargs)
        self.chunk_size = chunk_size

    def __iter__(self):
        return self.req.iter_content(self.chunk_size)

    def as_stream(self):
        """
        Returns a stream of the file contents.

        :return: IteratorToStream
        """
        return IteratorToStream(iter(self), on_update=partial(self.pbar.update, self.chunk_size))
