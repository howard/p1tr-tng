from p1tr.plugin import *

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
        print('[' + server + channel + '] <' + user + '> ' + message)

    def on_join(self, server, channel):
        print('[' + server + channel + '] ** The bot joined the channel.')

    def on_userjoin(self, server, channel, nick):
        print('[' + server + channel + '] ** ' + nick + ' joined the channel.')

    def on_connect(self, server):
        print('[' + server + '] Connected.')

    def on_disconnect(self, server):
        print('[' + server + '] Disconnected.')

    def on_quit(self):
        print(' *** BOT TERMINATED *** ')

    @command
    @require_op
    def disable_logging(self, server, channel, nick, args):
        pass #TODO

    @command
    @require_op
    def enable_logging(self, server, channel, nick, args):
        pass #TODO
