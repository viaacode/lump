import logging

from .cache import LocalCacher
from functools import partial
import time

_log = logging.getLogger(__name__)
# _log.propagate = True
_log.setLevel(logging.WARNING)
_log = _log.debug


def _get_cache_key(*args, **kwargs):
    return '||'.join(('|'.join(map(str, args)), '|'.join(kwargs.items())))


def log_call(logger: logging.Logger, log_level=logging.DEBUG, result=False):
    """
    Decorator to log all calls to decorated function to given logger

    >>> import logging, sys, io
    >>>
    >>> def get_logger():
    ...     logger = logging.getLogger('logger_name')
    ...     logger.setLevel(logging.DEBUG)
    ...     stream = io.StringIO()
    ...     ch = logging.StreamHandler(stream)
    ...     ch.setLevel(logging.DEBUG)
    ...     ch.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
    ...     logger.addHandler(ch)
    ...     return logger, stream
    >>>
    >>> logger, stream = get_logger()
    >>> @log_call(logger, logging.WARNING)
    ... def test(*args, **kwargs):
    ...     return 'result'
    >>> test('arg1', arg2='someval', arg3='someotherval')
    'result'
    >>> print(stream.getvalue().strip())
    WARNING:logger_name: test('arg1', arg2='someval', arg3='someotherval')
    >>> logger, stream = get_logger()
    >>> @log_call(logger, result=True)
    ... def test(*args, **kwargs):
    ...     return 'result'
    >>> test(arg2='someval', arg3='someotherval')
    'result'
    >>> print(stream.getvalue().strip())
    DEBUG:logger_name: test(arg2='someval', arg3='someotherval')
    DEBUG:logger_name: test returned: result
    """
    def _log_call(func: callable):
        def _(*args, **kwargs):
            arguments_format = []
            arguments_list = []
            if len(args):
                arguments_format.append('%s')
                arguments_list.append(', '.join([repr(a) for a in args]))
            if len(kwargs):
                arguments_format.append('%s')
                arguments_list.append(', '.join([k + '=' + repr(kwargs[k]) for k in kwargs]))

            arguments_format = '%s(%s)' % (func.__name__, ', '.join(arguments_format))

            logger.log(log_level, arguments_format, *arguments_list)
            result_ = func(*args, **kwargs)
            if result:
                logger.log(log_level, '%s returned: %s', func.__name__, result_)
            return result_
        return _
    return _log_call


def exception_redirect(new_exception_class, old_exception_class=Exception, logger=None):
    """
    Decorator to replace a given exception to another Exception class, with optional exception logging.

    >>>
    >>> class MyException(Exception):
    ...     pass
    >>>
    >>> @exception_redirect(MyException)
    ... def test():
    ...    raise Exception("test")
    >>>
    >>> test()
    Traceback (most recent call last):
    ...
    lump.decorators.MyException: test
    """
    def _decorator(func):
        def catch_and_redirect_exception(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except old_exception_class as e:
                if logger is not None:
                    logger.exception(e)
                raise new_exception_class(e) from None
        return catch_and_redirect_exception
    return _decorator


def memoize(f, cacher=None):
    """Usage:
    @memoize
    def someFunc():
    """
    if cacher is None:
        cacher = LocalCacher(max_items=50)

    def _cacher(*args, **kwargs):
        global _log
        x = _get_cache_key(*args, **kwargs)

        if x in cacher:
            _log('%s(%s): got: %s' % (memoize.__name__, f.__name__, str(x)))
            return cacher[x]

        res = f(*args, **kwargs)
        _log('%s(%s): set: %s' % (memoize.__name__, f.__name__, str(x)))
        cacher[x] = res
        return res

    return _cacher


def cache(cacher=None):
    """Usage:
    @cache(LocalCacher())
    def someFunc():

    > @cache
    > def test():
    >   print 'test'
    >   return 'result'
    >
    > test()
    test
    'result'
    > test()
    'result'
    """
    def _(f):
        return memoize(f, cacher=cacher)
    return _


def classcache(f):
    """Usage:
    > class SomeClass:
    >    @classcache
    >    def someFunc(self):
    """
    def _cacher(*args, **kwargs):
        global _log
        obj = args[0]
        cacher = obj.get_cacher()
        if not cacher:
            cacher = cache.DummyCacher()
        x = _get_cache_key(f.__name__, *args[1:], **kwargs)

        if hasattr(obj.__class__, 'classcacheVersionNumber'):
            x = '%s|v:%d' % (x, obj.__class__.classcacheVersionNumber)
            _log('version keyed: %s' % x)

        try:
            _log('%s.%s:%s got: %s' % (obj.__class__.__name__, f.__name__, classcache.__name__, str(x)))
            return cacher[x]
        except KeyError:
            pass

        res = f(*args, **kwargs)
        _log('%s.%s:%s set: %s' % (obj.__class__.__name__, f.__name__, classcache.__name__, str(x)))
        cacher[x] = res
        return res

    return _cacher


def retry(tries=5, logger=None, sleep=None):
    """
    Automagically retry the action

    >>> times = 0
    >>> @retry(5, logger=None)
    ... def a(n):
    ...     global times
    ...     times += 1
    ...     if times < n:
    ...        raise Exception("nope")
    ...     success = times
    ...     times = 0
    ...     return success
    >>> a(4)
    4
    >>> a(0)
    1
    >>> a(1)
    1
    >>> a(5)
    5
    >>> a(6)
    Traceback (most recent call last):
    ...
    Exception: nope
    """
    def _(f):
        def _decorator(*args, **kwargs):
            func = partial(f, *args, **kwargs)
            for i in range(tries):
                try:
                    return func()
                except Exception as e:
                    if logger:
                        logger.exception(e)
                    if i + 1 == tries:
                        raise e
                    if sleep is not None:
                        time.sleep(sleep)
        return _decorator
    return _

