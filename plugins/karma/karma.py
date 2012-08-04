from p1tr.plugin import *
from p1tr.helpers import *

class Karma(Plugin):
    """
    Modify people's karma by writing their nick, postfixed with ++ or --.
    Example: sebner++, P1tr--. You can access statistics using the karma
    command.
    """

    def __init__(self):
        Plugin.__init__(self)
        # Structure: {nick: (positive, negative)}
        self.karma = self.load_storage('karma')

    @command
    def karma(self, server, channel, nick, params):
        """
        Usage: karma [NICK] - delivers statistics about karma. If NICK is
        supplied, the specified NICK's statistics will be displayed instead,
        if available.
        """

    @command
    def nirvana(self, server, channel, nick, params):
        """
        Usage: nirvana NICK - sets the supplied NICK's karma to 0, so the user
        can finally enter long-awaited Nirvana.
        """
        user = nick.split('!')[0]
        if not user in self.karma:
            return '%s already has a clean slate.' % user
        del self.karma[user]
        return "%s's karma has been neutralized." % user

    def on_privmsg(self, server, channel, nick, message):
        """Listens for nick++ and nick--.
