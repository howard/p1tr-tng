from plugin import *
import subprocess

class Unix(Plugin):

    @command
    def fortune(self, server, channel, nick, params):
        """Prints a random fortune cookie."""
        process = subprocess.Popen('fortune', shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        stdout_value, stderr_value = process.communicate()
        return ' '.join(stdout_value.decode('utf-8').split())
