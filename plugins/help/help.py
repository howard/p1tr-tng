import inspect
from p1tr.helpers import clean_string, pretty_list
from p1tr.plugin import *

@meta_plugin
class Help(Plugin):
    """Provides help for all plugins by accessing their docstrings."""

    @command
    def help(self, server, channel, nick, params):
        """
        Usage: help PLUGIN [COMMAND] - prints a help message. If only PLUGIN is
        specified, you get general plugin information and a list of available
        commands. Otherwise, the help for the specific COMMAND of the PLUGIN is
        provided. If PLUGIN can't be found, I will look for a command with that
        name.
        """
        if len(params) < 1:
            return clean_string(self.help.__doc__)
        if len(params) < 2:
            if params[0] in self.bot.plugins: # Plugin found
                help_msg = clean_string(self.bot.plugins[params[0]].__doc__ or \
                        'Sorry, no help message available.')
                commands = sorted(list(name \
                        for name, member \
                        in inspect.getmembers(self.bot.plugins[params[0]])
                        if hasattr(member, '__annotations__') \
                                and 'command' in member.__annotations__))
                if len(commands) > 0:
                    help_msg += ' Commands: %s' % pretty_list(commands)
                return clean_string(help_msg)
            elif params[0] in self.bot.commands: # Command found
                return clean_string(getattr(
                    self.bot.commands[params[0]], params[0]).__doc__ or \
                            'Sorry, no help message available.')
            else:
                return 'Plugin or command "%s" not found.' % params[0]
        # Only Plugin->Command left now. Try to find it...
        if params[1] in self.bot.commands and \
                self.bot.commands[params[1]].__class__.__name__.lower() \
                == params[0]:
            return clean_string(getattr(
                self.bot.plugins[params[0]], params[1]).__doc__ or \
                        'Sorry, no help message available.')
        # If everything fails:
        return 'Command "%s" from plugin "%s" not found.' % (params[1],
                params[0])

    @command
    def list_commands(self, server, channel, nick, params):
        """Lists all available commands."""
        return pretty_list(self.bot.commands.keys())

    @command
    def list_plugins(self, server, channel, nick, params):
        """
        Lists all active plugins. Plugins on the global- or server-wide
        blacklist are not shown.
        """
        return pretty_list(self.bot.plugins.keys())
