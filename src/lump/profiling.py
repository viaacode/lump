import logging
import time


class timeit:
    """Helper class to easily report long running processes.
    Usage:

        >>> import logging, sys, time
        >>> logging.basicConfig(level=logging.WARNING)
        >>> logger = logging.getLogger('test')
        >>> logger.setLevel(logging.WARNING)
        >>> logger.addHandler(logging.StreamHandler(sys.stdout))
        >>> with timeit("Took a long time", 1000, logger=logger):
        ...    time.sleep(2)
        Took a long time: 2...ms
        >>> with timeit("Took a long time", 1000, logger=logger):
        ...    pass

    Or alternatively you can:

        >>> timer = timeit()
        >>> time.sleep(1)
        >>> print(timer.elapsed())
        100...
        >>> timer.restart()
        >>> print(timer.elapsed())
        0...
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    postfix = ': %dms'

    def __init__(self, text=None, min_time=None, callback=None, logger=None, postfix=None):
        """
        :param text: str
        :param min_time: int Minimum duration to start reporting in milliseconds
        :param callback: callable
        """
        self.text = text
        self.min_time = min_time
        self.start = time.monotonic()
        if logger is not None:
            self.logger = logger
        if postfix is not None:
            self.postfix = postfix
        self.callback = self._default_callback if callback is None else callback

    def restart(self):
        self.start = time.monotonic()

    def elapsed(self):
        return (time.monotonic() - self.start)*1000

    def __enter__(self):
        self.restart()

    def __exit__(self, kind, value, traceback):
        ms = self.elapsed()
        is_slow = self.min_time is not None and ms > self.min_time
        self.callback(ms, is_slow, self.text, kind, value, traceback)

    def get_logger(self):
        return self.logger

    def _default_callback(self, ms, is_slow, text, kind, value, traceback):
        postfix = self.postfix
        if self.min_time is None:
            self.logger.info(text + postfix, ms)
        elif is_slow:
            self.logger.warning(text + postfix, ms)
