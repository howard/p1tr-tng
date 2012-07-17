from plugin import *

@meta_plugin
class Help(Plugin):
    """Provides help for all plugins by accessing their docstrings."""

    @command
    def help(self, server, channel, nick, params):
        """
        Usage: help PLUGIN [COMMAND] - prints a help message. If only PLUGIN is
        specified, you get general plugin information. Otherwise, the help for
        the specific COMMAND of the PLUGIN is provided. If PLUGIN can't be
        found, I will look for a command with that name.
        """
        if len(params) < 1:
            return clean_string(self.help.__doc__)
        if len(params) < 2:
            if params[0] in self.bot.plugins: # Plugin found
                return clean_string(self.bot.plugins[params[0]].__doc__)
            elif params[0] in self.bot.commands: # Command found
                return clean_string(getattr(
                    self.bot.commands[params[0]], params[0]).__doc__)
            else:
                return 'Plugin or command "' + params[0] + '" not found.'
        # Only Plugin->Command left now. Try to find it...
        if params[1] in self.bot.commands and \
                self.bot.commands[params[1]].__class__.__name__.lower() \
                == params[0]:
            return clean_string(getattr(
                self.bot.plugins[params[0]], params[1]).__doc__)
        # If everything fails:
        return 'Command "' + params[1] + '" from plugin "' + params[0] + \
                '" not found."'


