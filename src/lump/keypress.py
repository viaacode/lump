from multiprocessing import Process
from collections import namedtuple
from functools import partial
import sys
import termios
import tty
import logging

logger = logging.getLogger(__name__)
Option = namedtuple('Option', ('character', 'description', 'callback'))


class KeyPressOptions:
    def __init__(self, auto_include_help=None):
        self._options = {}
        self.help_title = 'Available Options'
        if auto_include_help is None or auto_include_help:
            self.register('?', self.print_help, 'provides a help message of possible options')

    def print_help(self):
        print(self.help_title)
        print('=' * len(self.help_title))
        print()
        print('\n\r'.join(['\t'.join((option.character, option.description))
                           for option in self._options.values()]))
        print()
        if len(self._options) == 1:
            logger.warning('No options currently registered')

    def register(self, character, callback, description):
        if len(character) != 1 or type(character) is not str:
            raise ValueError("Expected character to be a string of length 1")

        if character in self._options:
            raise ValueError("An action for %r has already been defined" % (character,))

        self._options[character] = Option(character, description, callback)

    def __call__(self, char):
        if char not in self._options:
            return
        return self._options[char].callback()


class KeyPressHandler:
    """
    A handler that reads keypresses in a separate process, and handles any actions
    that may be associated with that keypress.
    """
    def __init__(self):
        self.process = None
        self.options = KeyPressOptions()

    def register(self, *args, **kwargs):
        return self.options.register(*args, **kwargs)

    def start(self):
        """
        Start the process for handling keypresses, this should be the last thing
        called as it will block further script execution...
        """
        global print
        # dirty solution to keep proper formatting of output
        print = partial(print, end='\n\r')
        self.process = Process(target=self.listen)
        self.process.start()
        self.process.join()

    def listen(self):
        sys.stdin = open(0)
        while True:
            try:
                char = self._get_char()
                self.options(char)
            except (KeyboardInterrupt, EOFError, SystemExit) as e:
                return
            except Exception as e:
                logger.exception(e)

    @staticmethod
    def _get_char():
        """
        Read a character from stdin
        :return: Character
        :rtype: str
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
