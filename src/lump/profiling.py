import logging
import time


class timeit:
    """Helper class to easily report long running processes.
    Usage:

        with timeit("Took a long time", 5000):
            time.sleep(6)

    Or alternatively you can:

        timer = timeit()
        ...
        print(timer.elapsed())
        timer.restart()
        ...
        print(timer.elapsed())
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    def __init__(self, text=None, min_time=None, callback=None):
        """
        :param text: str
        :param min_time: int Minimum duration to start reporting in milliseconds
        :param callback: callable
        """
        self.text = text
        self.min_time = min_time
        self.start = time.monotonic()
        self.callback = self._default_callback if callback is None else callback

    def restart(self):
        self.start = time.monotonic()
        return self.start

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
        if self.min_time is None:
            self.logger.info(text + ': %dms', ms)
        elif is_slow:
            self.logger.warning(text + ': %dms', ms)
