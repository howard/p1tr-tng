from p1tr.plugin import *
import re
import subprocess

def get_command_output(command):
        """Returns the output of a console command. Discards STDERR."""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        stdout_value, stderr_value = process.communicate()
        return clean_string(stdout_value.decode('utf-8'))

class Unix(Plugin):
    """Provides access to some classic unix commands."""
    
    def __init__(self):
        Plugin.__init__(self)
        self._morse_pattern = re.compile(r'^[a-zA-Z0-1 \.\-]*$')

    @command
    def fortune(self, server, channel, nick, params):
        """Prints a random fortune cookie."""
        return get_command_output('fortune')

    @command
    def uname(self, server, channel, nick, params):
        """
        Displays information about the operating system, as provided by the
        uname -a command.
        """
        return get_command_output('uname -a')

    @command
    def uptime(self, server, channel, nick, params):
        """Prints operating system uptime."""
        return get_command_output('uptime')

    @command
    def pom(self, server, channel, nick, params):
        """
        Usage: pom [YYYYMMDDHH] - Current moon phase. You can optionally provide
        a date in the given format to get the moon phase at this point in time.
        """
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
