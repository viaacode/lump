import collections
import logging
import os
import hashlib
import zlib
import pickle
import time

logger = logging.getLogger(__name__)


class DictCacher(dict):
    """
    Simple 'Local' cacher using a new dict... Usable to re-use same interface
    for other classes...

    >>> cache = DictCacher()
    >>> cache['test'] = True
    >>> cache['test']
    True
    >>> 'test' in cache
    True
    >>> cache['test2'] = 2
    >>> 'test2' in cache
    True
    >>> cache['test3'] = 'three'
    >>> 'test3' in cache
    True
    >>> cache['test3']
    'three'
    >>> 'test' in cache
    True
    """
    pass


class WrapperCacher:
    """
    Wrapper class for cache classes that use .get, .set and .has_key methods
    instead of item assignments, eg. django FileBasedClass
    """
    def __init__(self, obj,  timeout=None, version=None):
        self.obj = obj
        self.extra_write_arguments = {}
        if timeout is not None:
            self.extra_write_arguments['timeout'] = timeout
        if version is not None:
            self.extra_write_arguments['version'] = version

    def __setitem__(self, k, v):
        return self.obj.set(k, v, **self.extra_write_arguments)

    def __getitem__(self, k):
        return self.obj.get(k)

    def __contains__(self, k):
        return k in self.obj


class LocalCacher:
    """
    Simple 'Local' cacher with a maximum amount of items

    >>> cache = LocalCacher(2)
    >>> cache.max_items
    2
    >>> cache['test'] = True
    >>> cache['test']
    True
    >>> 'test' in cache
    True
    >>> cache['test2'] = 2
    >>> 'test2' in cache
    True
    >>> cache['test3'] = 'three'
    >>> 'test3' in cache
    True
    >>> cache['test3']
    'three'
    >>> 'test' in cache
    False
    >>> cache['test']
    Traceback (most recent call last):
    ...
    KeyError: 'test'
    """
    def __init__(self, max_items=None):
        self.dict = collections.OrderedDict()
        self.max_items = max_items

    def __setitem__(self, k, v):
        if self.max_items is not None and len(self.dict) >= self.max_items:
            self.dict.popitem(last=False)
        self.dict[str(k)] = v

    def __getitem__(self, k):
        return self.dict[str(k)]

    def __contains__(self, k):
        return str(k) in self.dict


class DummyCacher:
    """
    >>> cache = DummyCacher()
    >>> cache['test'] = True
    >>> print(cache['test'])
    Traceback (most recent call last):
    ...
    KeyError: 'test'
    >>> 'test' in cache
    False
    >>> cache['test2'] = 2
    >>> 'test2' in cache
    False
    """
    @staticmethod
    def __getitem__(i):
        raise KeyError(i)

    @staticmethod
    def __setitem__(k, v):
        return False

    @staticmethod
    def __contains__(k):
        return False


class FileCacher:
    suffix = '.cache'

    def __init__(self, path, timeout=None, hasher=None, version=None):
        self._path = os.path.abspath(path)
        self._timeout = timeout
        self._createpath()
        if hasher is False:
            hasher = type(self)._reflect_hasher_func
        if hasher is None:
            hasher = type(self)._default_hasher_func

        self._hasher = hasher
        self._version = version

        self._compress = zlib.compress
        self._decompress = self._zlib_decompress

        # self._compress = self._reflect_hasher_func
        # self._decompress = self._reflect_hasher_func

    @staticmethod
    def _zlib_decompress(data):
        try:
            return zlib.decompress(data)
        except zlib.error:
            return None

    def _createpath(self):
        if os.path.exists(self._path):
            return
        try:
            os.makedirs(self._path, 0o700)
        except FileExistsError:
            pass

    @staticmethod
    def _reflect_hasher_func(k):
        return k

    @staticmethod
    def _default_hasher_func(k):
        if type(k) is not bytes:
            k = bytes(k, encoding='utf-8')
        return hashlib.md5(k).hexdigest()

    def _filename(self, k):
        if self._version is not None:
            filename = 'v%d_' % (self._version,)
        else:
            filename = ''
        filename += '%s%s' % (self._hasher(k), type(self).suffix)
        return os.path.join(self._path, filename)

    def __setitem__(self, k, v):
        filename = self._filename(k)

        with open(filename, 'wb') as f:
            to_write = pickle.dumps(v, pickle.HIGHEST_PROTOCOL)
            to_write = self._compress(to_write)
            f.write(to_write)

    def __getitem__(self, k):
        filename = self._filename(k)
        err = KeyError(k)

        try:
            age = time.time() - os.path.getmtime(filename)
        except FileNotFoundError:
            raise err

        if self._timeout is not None and age > self._timeout:
            os.remove(filename)
            raise err

        with open(filename, 'rb') as f:
            to_return = f.read()
            to_return = self._decompress(to_return)

            if to_return is None:
                os.remove(filename)
                raise err

            to_return = pickle.loads(to_return)

        return to_return

    def __contains__(self, k):
        try:
            self.__getitem__(k)
            return True
        except KeyError:
            return False


class CacheProxy:
    def __init__(self, cacher):
        self.cacher = cacher

    def __getitem__(self, key):
        return self.cacher.__getitem__(key)

    def __setitem__(self, key, value):
        return self.cacher.__setitem__(key, value)

    def __contains__(self, item):
        return self.cacher.__contains__(item)


class CacheLocker(CacheProxy):
    def __init__(self, cacher):
        super().__init__(cacher)
        self.cur_get = set()
        self.cur_set = set()
        self.max_wait = 500

    def __getitem__(self, k):
        i = 0
        while (k in self.cur_get or k in self.cur_set) and i < self.max_wait:
            time.sleep(0.01)
            if i == 10:
                logger.info('Long sleep for %s', k)
            i += 1

        if i > 10:
            logger.warning('get %s slept for %dms', k, i * 10)

        try:
            self.cur_get.add(k)
            result = super().__getitem__(k)
        except KeyError as e:
            self.cur_get.remove(k)
            raise e
        except Exception as e:
            logger.error(e)
            self.cur_get.remove(k)
            raise KeyError(k)
            # raise e

        self.cur_get.remove(k)
        return result

    def __setitem__(self, k, v):
        i = 0
        while (k in self.cur_set) and i < self.max_wait:
            time.sleep(0.01)
            if i == 10:
                logger.info('Long sleep for %s', k)
            i += 1

        if i > 10:
            logger.warning('set %s slept for %dms', k, i * 10)

        self.cur_set.add(k)
        try:
            super().__setitem__(k, v)
        except Exception as e:
            # logger.error(e)
            raise KeyError(k)

        try:
            self.cur_set.remove(k)
        except KeyError:
            pass


class CacheAggregate:
    def __init__(self, cachers):
        self.cachers = cachers

    def __contains__(self, k):
        return any(k in cacher for cacher in self.cachers)

    def __getitem__(self, k):
        cachers_done = []
        for cacher in self.cachers:
            try:
                start_time = time.monotonic()
                res = cacher[k]
                # temp fix to not need to bump cache, accidentally wrote some KeyErrors to cache
                if type(res) is KeyError:
                    raise res

                logger.debug('GET FROM %s: %s %.4fs', type(cacher), k, time.monotonic() - start_time)

                # we got a result, write result to previous cachers as well
                for to_migrate_cache in cachers_done:
                    to_migrate_cache[k] = res

                return res
            except KeyError:
                cachers_done.append(cacher)
                pass

        raise KeyError(k)

    def __setitem__(self, k, v):
        for cacher in self.cachers:
            try:
                cacher[k] = v
            except Exception as e:
                logger.warning("cacheaggregator set exception %s", e)


class OptimizedFileCacher(CacheProxy):
    def __init__(self, path, max_local_items=None, *args, **kwargs):
        if max_local_items is None:
            max_local_items = 5

        cacher = CacheAggregate([
            LocalCacher(max_local_items),
            FileCacher(path=path, *args, **kwargs)
        ])
        cacher = CacheLocker(cacher)

        super().__init__(cacher)
