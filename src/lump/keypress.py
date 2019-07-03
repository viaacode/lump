from multiprocessing import Process
from textwrap import dedent
from collections import namedtuple
import sys
import termios
import tty
import logging
from lump.csv import reader, UnclosedQuoteError
from io import StringIO

logger = logging.getLogger(__name__)
Option = namedtuple('Option', ('input', 'description', 'callback'))

stdout = sys.stdout


class Options:
    def __init__(self, auto_include_help=None):
        self._options = {}
        self.help_title = 'Available Options'
        self._init_(auto_include_help)

    def _init_(self, auto_include_help=None):
        if auto_include_help is None or auto_include_help:
            self['help'] = self.print_help

    def print_help(self):
        """
        provides a help message of possible options
        """
        print(self.help_title)
        print('=' * len(self.help_title))
        print()
        print('\n'.join(['\t'.join((option.input, option.description))
                         for option in self._options.values()]))
        print()
        if len(self._options) == 1:
            logger.warning('No options currently registered')

    def register(self, value, callback, description):
        if type(value) is not str or len(value) == 0:
            raise ValueError("The value needs to be a string with length > 0")

        if value in self._options:
            raise ValueError("An action for %r has already been defined" % (value,))

        self._options[value] = Option(value, description, callback)

    def run(self, value, *args):
        if value not in self:
            logger.warning('Unknown command %r, possible commands: %s', value, ', '.join(self._options.keys()))
            return
        return self[value].callback(*args)

    def __contains__(self, item):
        return item in self._options

    def __getitem__(self, item):
        return self._options[item]

    def __setitem__(self, key, value):
        self.register(key, value, dedent(value.__doc__).strip())


class CharOptions(Options):
    def _init_(self, auto_include_help=None):
        if auto_include_help is None or auto_include_help:
            self['?'] = self.print_help

    def _process(self, char):
        self.run(char)

    def register(self, value, callback, description):
        if len(value) != 1 or type(value) is not str:
            raise ValueError("Expected character to be a string of length 1")

        super().register(value, callback, description)


class ComplexOptions(Options):
    """
    Options with possibility of arguments, interpreted with the whitespace
    dialect csv parser
    """

    def run(self, value, *args):
        try:
            args = next(iter(reader(StringIO(value), dialect='whitespace')))
        except StopIteration:
            # empty line
            return
        value = args.pop(0)
        super().run(value, *args)


class InteractiveTerminalHandler:
    """
    A handler that reads commands from stdin in a separate process, and handles
    any actions that may be associated with it.
    """

    def _process(self, char):
        if char == '\x7f':
            # rudimentary backspace support
            self._buffer = self._buffer[:-1]
            stdout.write('\n')
            stdout.write(self._buffer)
            stdout.flush()
            return

        stdout.write(char)
        stdout.flush()

        if char == '\n':
            try:
                self.options.run(self._buffer)
                self._buffer = ''
                return
            except UnclosedQuoteError:
                self._buffer += char
                return
            except BaseException as e:
                logger.exception(e)
                self._buffer = ''
                return

        self._buffer += char

    def __init__(self):
        self.process = None
        self._init_()

    def _init_(self):
        self.options = ComplexOptions()
        self._buffer = ''

    def register(self, *args, **kwargs):
        return self.options.register(*args, **kwargs)

    def start(self):
        """
        Start the process for handling keypresses, this should be the last thing
        called as it will block further script execution...
        """
        self.process = Process(target=self.listen)
        self.process.start()
        self.process.join()

    def listen(self):
        sys.stdin = open(0)
        while True:
            try:
                char = self._get_char()
                self._process(char)
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


class KeyPressHandler(InteractiveTerminalHandler):
    """
    A handler that reads keypresses from stdin in a separate process, and
    handles any actions that may be associated with that keypress.
    """
    def _init_(self):
        self.options = CharOptions()

    def register(self, *args, **kwargs):
        return self.options.register(*args, **kwargs)

    def _process(self, char):
        self.options.run(char)
