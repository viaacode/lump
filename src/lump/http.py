from tqdm import tqdm
import requests
from functools import partial
from lump.stream import IteratorStream
from hashlib import sha1
import uuid
from lxml import objectify


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
        self._iterator = self.req.iter_content(self.chunk_size)

    def __iter__(self):
        return self._iterator

    def __next__(self):
        return next(self._iterator)

    def as_stream(self):
        """
        Returns a stream of the file contents.

        :return: :class:`lump.stream.IteratorStream`
        """
        return IteratorStream(self, on_update=partial(self.pbar.update, self.chunk_size))


def dbus_connect(host, user, password):
    """
    Minimalistic D-Bus login

    :param host: Host (including schema) to connect to
    :param user: Login username
    :param password: Login password
    :return: request.Session
    """
    conn = requests.Session()
    login_url = host + '/login'
    login_data = dict(dbus="AUTH DBUS_COOKIE_SHA1 %s" % (user,))
    response = conn.post(login_url, data=login_data)
    resp = objectify.fromstring(response.content)
    dbus = resp['items']['item']['dbus']

    resp = str(dbus).split(' ')

    if resp[0] != 'DATA':
        raise ValueError(str(dbus))

    challenge = resp[3]
    random = uuid.uuid4().hex[:10]
    challenge_response = sha1(bytes(':'.join([challenge, random, password]), 'utf-8')).hexdigest()
    login_data = dict(dbus='DATA %s %s' % (random, challenge_response))
    response = conn.post(login_url, data=login_data)
    resp = objectify.fromstring(response.content)
    dbus = resp['items']['item']['dbus']
    resp = str(dbus).split(' ')
    if resp[0] != 'OK':
        raise ValueError(str(dbus))
    return conn
