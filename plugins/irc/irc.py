from p1tr.helpers import clean_string
from p1tr.plugin import *

@meta_plugin
class Irc(Plugin):
    """Provides commands for basic IRC operations."""

    @command
    @require_master
    def nick(self, server, channel, nick, params):
        """Usage: nick NEW_NICKNAME - changes the bot's nickname."""
        if len(params) < 1:
            return clean_string(self.nick.__doc__)
        self.bot.client.send('NICK', params[0])

    @command
    @require_master
    def join(self, server, channel, nick, params):
        """
        Usage: join #CHANNEL [PASSWORD] - the bot will enter the specified
        channel. A password may be provided optionally, if it is required.
        """
        if len(params) < 1:
            return clean_string(self.join.__doc__)
        password = ''
        if len(params) > 1:
            password = params[0]
        self.bot.client.send('JOIN', params[0], password)

    @command
    @require_op
    def part(self, server, channel, nick, params):
        """
        Usage: part [#CHANNEL] - asks the bot to leave the current channel.
        Optionally, a channel may be specified if it should be left instead of
        the current one.
        """
        if len(params) > 0:
            channel = params[0]
        self.bot.client.send('PART', channel)
