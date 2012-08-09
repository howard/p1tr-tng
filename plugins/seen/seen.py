import datetime
from p1tr.helpers import clean_string, humanize_time
from p1tr.plugin import *

class Seen(Plugin):
    """
    Tracks all user's most recent time of activity.
    """

    def __init__(self):
        Plugin.__init__(self)
        # Storage format: key = username,
        # value = (timestamp, channel, lastActivity)
        self.memory = self.load_storage('memory')

    @command
    def seen(self, server, channel, nick, params):
        """
        Usage: seen NICK - Shows how long ago the given nick was seen for the
        last time, and what they were doing then.
        """
        if len(params) < 1:
            return clean_string(self.seen.__doc__)
        subject = params[0]
        if not subject in self.memory:
            return 'I have not seen %s before.' % subject
        entry = self.memory[subject]
        return '%s was last seen %s ago in %s, %s.' % (subject,
                humanize_time(datetime.datetime.now() - entry[0]),
                entry[1], entry[2])

    def _remember(self, channel, nick, activity):
        """Helper for saving user activities to memory."""
        self.memory[nick.split('!')[0]] = (datetime.datetime.now(), channel,
                activity)

    def on_privmsg(self, server, channel, nick, message):
        self._remember(channel, nick, 'saying "%s"' % message)

    def on_useraction(self, server, channel, nick, message):
        self._remember(channel, nick,
                'saying "* %s %s"' % (nick.split('!')[0], message))

    def on_userjoin(self, server, channel, nick):
        self._remember(channel, nick, 'joining the channel')

    def on_userpart(self, server, channel, nick, message):
        activity = 'leaving the channel'
        if len(message) > 0:
            activity += ', saying "%s"' % message
        self._remember(channel, nick, activity)

    def on_userkicked(self, server, channel, nick, reason):
        activity = 'getting kicked'
        if len(reason) > 0:
            activity += ' because: %s' % reason
        self._remember(channel, nick, activity)

    def on_userrenamed(self, server, oldnick, newnick):
        self._remember('some channel', oldnick, 'changing his nick to %s' %
                newnick)
