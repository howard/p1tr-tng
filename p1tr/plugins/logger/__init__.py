"""
Conversation logging plugin.

Conversations are logged by default to a file in the bot's home directory. This
can be disabled by adding logger.log = no to the channel's section in the
configuration file.
"""

from plugin import *

class Logger(Plugin):

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
