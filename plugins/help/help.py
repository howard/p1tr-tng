import inspect
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
                    help_msg += ' Commands: ' + ' '.join(commands)
                return clean_string(help_msg)
            elif params[0] in self.bot.commands: # Command found
                return clean_string(getattr(
                    self.bot.commands[params[0]], params[0]).__doc__ or \
                            'Sorry, no help message available.')
            else:
                return 'Plugin or command "' + params[0] + '" not found.'
        # Only Plugin->Command left now. Try to find it...
        if params[1] in self.bot.commands and \
                self.bot.commands[params[1]].__class__.__name__.lower() \
                == params[0]:
            return clean_string(getattr(
                self.bot.plugins[params[0]], params[1]).__doc__ or \
                        'Sorry, no help message available.')
        # If everything fails:
        return 'Command "' + params[1] + '" from plugin "' + params[0] + \
                '" not found."'
    
    @command
    def list_commands(self, server, channel, nick, params):
        """Lists all available commands."""
        return ' '.join(self.bot.commands.keys())

    @command
    def list_plugins(self, server, channel, nick, params):
        """
        Lists all active plugins. Plugins on the global- or server-wide
        blacklist are not shown.
        """
        return ' '.join(self.bot.plugins.keys())
