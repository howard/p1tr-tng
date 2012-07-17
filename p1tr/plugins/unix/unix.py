from plugin import *
import subprocess

def get_command_output(command):
        """Returns the output of a console command. Discards STDERR."""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        stdout_value, stderr_value = process.communicate()
        return ' '.join(stdout_value.decode('utf-8').split())

class Unix(Plugin):
    """Provides access to some classic unix commands."""
    
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

