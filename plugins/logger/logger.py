from p1tr.plugin import *
from p1tr.logwrap import plain, info

class Logger(Plugin):
    """
    Conversation logging plugin.

    Conversations are logged by default to a file in the bot's home directory. This
    can be disabled by adding logger.log = no to the channel's section in the
    configuration file.
    """
    
    _restricted_channels = []

    def __init__(self):
        Plugin.__init__(self)

    def load_settings(self, config):
        """
        Overriding default behavior since the logger.log setting is 
        context-sensitive.
        """
        for section in config:
            if 'logger.log' in section and section.getboolean('logger.log'):
                self._restricted_channels.append(section)

    def on_privmsg(self, server, channel, user, message):
        plain('<' + user.split('!')[0] + '> ' + message,
                server=server, channel=channel)

    def on_join(self, server, channel):
        plain(' ** The bot joined the channel.', server=server, channel=channel)

    def on_part(self, server, channel, message):
        plain(' ** The bot left the channel.', server=server, channel=channel)

    def on_modechanged(self, server, channel):
        #TODO
        pass

    def on_topicchanged(self, server, channel, nick, oldtopic, newtopic):
        plain(' ** Topic changed; old: ' + oldtopic, server=server,
                channel=channel)
        plain(' ** Topic changed; new: ' + newtopic, server=server,
                channel=channel)

    def on_kicked(self, server, channel, reason):
        plain(' ** Bot was kicked: ' + reason or 'no reason', server=server,
                channel=channel)

    def on_userjoin(self, server, channel, nick):
        plain(' ** ' + nick + ' joined the channel.', server=server,
                channel=channel)

    def on_userpart(self, server, channel, nick, message):
        plain(' ** ' + nick + ' left the channel: ' + message or 
                'no part message', server=server, channel=channel)

    def on_userkicked(self, server, channel, nick, reason):
        plain(' ** ' + nick + ' was kicked: ' + reason or 'no reason',
                server=server, channel=channel)

    def on_userrenamed(self, server, channel, oldnick, newnick):
        plain(' ** ' + oldnick + ' is now known as ' + newnick, server=server,
                channel=channel)

    def on_useraction(self, server, channel, nick, message):
        plain(' * ' + nick.split('!')[0] + ' ' + message, server=server,
                channel=channel)

    def on_connect(self, server):
        info('Connected to the server.', server=server)

    def on_disconnect(self, server):
        info('Disconnected from the server.', server=server)

    def on_quit(self):
        info('Terminating plugins.')

    @command
    @require_op
    def disable_logging(self, server, channel, nick, args):
        """
        Usage: disable_logging [#CHANNEL] - temporarily disables logging; if a
        channel is specified, logging for this channel is disabled. Otherwise,
        the current channel is used. The user must have at least OP in the
        affected channel.
        """
        if len(args) > 0:
            channel = args[0]
        self._restricted_channels.append(channel)

    @command
    @require_op
    def enable_logging(self, server, channel, nick, args):
        """
        Usage: enable_logging [#CHANNEL] - enables logging; if a channel is
        specified, logging for this channel is enabled. Otherwise, the current
        channel is used. The user must have at least OP in the affected
        channel.
        """
        if len(args) > 0:
            channel = args[0]
        self._restricted_channels.remove(channel)
