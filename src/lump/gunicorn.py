from gunicorn.app.base import BaseApplication
import multiprocessing
from lump.keypress import InteractiveTerminalHandler
from multiprocessing import Process
import psutil
import logging
import os
from lump.humanreadable import format_metric

logger = logging.getLogger(__name__)


class GunicornApplication(BaseApplication):
    """
    Usable to run a gunicorn application with sensible defaults
    """

    applied_automagically = ('workers', 'bind')

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app

        for name in self.applied_automagically:
            self._apply_automagically(name)

        self._init_()
        super().__init__()

    def _init_(self):
        """
        Meant to be overriden, will be called on class initialization
        """
        pass

    def _apply_automagically(self, name):
        option_name = 'auto_%s' % (name,)
        value = True
        try:
            value = self.options[option_name]
        except KeyError:
            pass

        if value:
            option_value = getattr(self, '_' + option_name)()
            logger.debug('Auto-determined value for option %r to be %r', name, option_value)
            self.options[name] = option_value

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

    @staticmethod
    def _auto_workers():
        return (multiprocessing.cpu_count() * 2) + 1

    @staticmethod
    def _auto_bind():
        return '0.0.0.0:8080'


class GunicornInteractiveApplication(GunicornApplication):
    """
    Usable to run a gunicorn application with sensible default and the possibility
    to provide some general options using commands (e.g. memory information).
    """

    def _init_(self):
        self.main_pid = os.getpid()
        self.main_process = psutil.Process(self.main_pid)
        self.keypress_handler = InteractiveTerminalHandler()
        self.keypress_handler.register('mem', self._show_memory, 'Output current memory usage')

    def run(self):
        process = Process(target=super().run)
        process.start()
        self.keypress_handler.start()
        process.join()

    def print_help(self):
        self.keypress_handler.options.print_help()

    def _show_memory(self):
        print('Current memory usage: %s' % (format_metric(self.main_process.memory_info().rss),))
