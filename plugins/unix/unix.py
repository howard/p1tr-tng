from p1tr.helpers import clean_string
from p1tr.plugin import *
import os
import re
import subprocess

def get_command_output(command):
    """Returns the output of a console command. Discards STDERR."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    stdout_value, stderr_value = process.communicate()
    return clean_string(stdout_value.decode('utf-8'))

def check_available(command):
    """Returns True if the command is available on the system."""
    if os.name != 'posix':
        return False
    return len(get_command_output('which %s' % command)) > 0


class Unix(Plugin):
    """Provides access to some classic unix commands."""

    def __init__(self):
        Plugin.__init__(self)
        self._morse_pattern = re.compile(r'^[a-zA-Z0-1 \.\-]*$')

    @command
    def fortune(self, server, channel, nick, params):
        """Prints a random fortune cookie."""
        if not check_available('fortune'):
            return 'The fortune command is not installed on my host.'
        return get_command_output('fortune')

    @command
    def uname(self, server, channel, nick, params):
        """
        Displays information about the operating system, as provided by the
        uname -a command.
        """
        if not check_available('uname'):
            return 'The uname command is not installed on my host.'
        return get_command_output('uname -a')

    @command
    def uptime(self, server, channel, nick, params):
        """Prints operating system uptime."""
        if not check_available('uptime'):
            return 'The uptime command is not installed on my host.'
        return get_command_output('uptime')

    @command
    def pom(self, server, channel, nick, params):
        """
        Usage: pom [YYYYMMDDHH] - Current moon phase. You can optionally provide
        a date in the given format to get the moon phase at this point in time.
        """
        if not check_available('pom'):
            return 'The pom command is not installed on my host.'
        if len(params) > 0:
            try:
                date = int(params[0])
            except ValueError:
                return 'Invalid date.'
            return get_command_output('pom ' + date)
        return get_command_output('pom')

    @command
    def morse(self, server, channel, nick, params):
        """
        Usage: morse decode|encode TEXT - translates a given TEXT to and from
        morse code.
        """
        if not check_available('morse'):
            return 'The morse command is not installed on my host.'
        if len(params) < 2 or not params[0] in ('decode', 'encode'):
            return clean_string(self.morse.__doc__)
        text = ' '.join(params[1:])
        # Check for illegal characters to avoid shell access.
        if not self._morse_pattern.match(text):
            return 'Illegal characters in input text.'
        if params[0] == 'decode':
            return get_command_output('morse -d -- ' + text)
        if params[0] == 'encode':
            return get_command_output('morse -s -- ' + text)

    @command
    def number(self, server, channel, nick, params):
        """Usage: number NUMBER - translates arabic numerals to english text."""
        if not check_available('number'):
            return 'The number command is not installed on my host.'
        if len(params) < 1:
            return clean_string(self.number.__doc__)
        try:
            return get_command_output('number -l ' + str(int(params[0])))
        except ValueError:
            return 'This is not a real number.'

    @command
    def caesar(self, server, channel, nick, params):
        """
        Usage: caesar ROTATION MESSAGE - encrypts a MESSAGE using the caesar
        cipher. ROTATION is the number by which the letters in MESSAGE are
        shifted.
        """
        if not check_available('caesar'):
            return 'The caesar command is not installed on my host.'
        if len(params) < 2:
            return clean_string(self.caesar.__doc__)
        rotation = 0
        try:
            rotation = str(int(params[0]))
        except ValueError:
            return 'Invalid rotation. Not a real number.'
        message = ' '.join(params[1:])
        if not self._morse_pattern.match(message):
            return 'Illegal characters in input text.'
        return get_command_output('echo ' + message + ' | caesar ' + rotation)
