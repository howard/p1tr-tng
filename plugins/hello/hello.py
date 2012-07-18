from p1tr.plugin import *

class Hello(Plugin):
    """
    A simple greeter. Easy demo plugin.
    """

    @command
    def hello(self, server, channel, nick, args):
        return 'Hello, ' + nick + '!'
