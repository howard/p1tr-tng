"""
Plugin base class and related utilities.
"""
import glob
import os.path

def load_by_name(plugin_name, config):
    """
    Attempts to load a plugin. The steps for that are as follows:
    1. Search for a directory named the all-lowercase version of plugin_name.
       The search order is:
        - Current working directory
        - P1tr home (as specified in config file)
        - P1tr install location (location of the main script)
       In all locations mentioned above, a "plugin" sub-directory is searched
       for a directory with the fitting name.
    2. If the directory was found, read the .py file with the same name and
       instantiate the class with the capitalized version of plugin_name, which
       should be defined in the file.
    3. The resulting object is checked, whether its class is derived from 
       Plugin.
    4. Apply plugin settings as specified in the configuration file to the
       plugin.
    5. The instance of the plugin is returned.
    If any step fails, a PluginError exception is thrown.

    The parameter config should be an instance of ConfigParser, which has
    already parsed the config file.
    """
    try:
        module = __import__('plugins.' + plugin_name + '.' + plugin_name)
    except ImportError:
        raise PluginError('Plugin "' + plugin_name + '" not found.')
    
    # Create instance and check type.
    instance = getattr(getattr(getattr(module, plugin_name), plugin_name), plugin_name.capitalize())()
    if not isinstance(instance, Plugin):
        raise PluginError('Invalid plugin: Not derived from Plugin.')

    # Apply settings and return plugin instance.
    instance.load_settings(config)
    return instance


# Decorators:
class command:
    """
    Plugin methods with this decorator are callable as irc commands. By default,
    the command name is the name of the method. The "name" decorator argument
    can change that. The command is then available in IRC by writing the signal
    character as defined in the configuration file, and the name of the command
    immediately after the character.
    """

    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        return func

class require_master:
    """
    Commands with this decorator are only executed if the caller is the
    bot master.
    """
    
    def __init__(self, func):
        self.func = func
        self.func.__annotations__['require_master'] = True

    def __call__(self, *args):
        return self.func(*args)

class require_op:
    """
    Commands with this decorator are only executed if the caller is op.
    """

    def __init__(self, func):
        self.func = func
        self.func.__annotations__['require_op'] = True

    def __call__(self, *args):
        return self.func(*args)

class require_voice:
    """
    Commands with this decorator are only executed if the caller is op
    or has voice.
    """

    def __init__(self, func):
        self.func = func
        self.func.__annotations__['require_voice'] = True

    def __call__(self, *args):
        return self.func(*args)

    
class PluginError(Exception):
    """
    Thrown when plugin loading fails.
    """


class Plugin:
    """
    Base class of all plugins.

    Inheriting from this class is necessary in order to create a working plugin.
    Consider this class abstract - do not instantiate!
    You may give your plugin functionality by overriding the methods of this
    class.

    Please note that the docstring of your plugin's class, which inherits from
    Plugin, is used to describe the plugin in the help message.
    """
    
    """
    Persistent key-value storage, is automatically populated on plugin load.
    """
    _storage = dict();
    """
    Plugin-specific settings; meant to be accessible to the plugin container.
    """
    _settings = dict();

    def __init__(self):
        """
        Always call this constructor first thing in your plugin's constructor.
        """
        # TODO: load settings and persistend storage

    def load_settings(self, config):
        """
        Extracts relevant information from the bot's configuration, which is
        provided as a configparser.ConfigParser object. This method is called
        automatically on plugin load, and on runtime config changes.

        By default, the entire config file is scanned for keys looking like
        pluginname.keyname. The value is then stored in the plugin instance's
        attribute _settings under the key keyname.

        If you need a different behavior, feel free to override this method.
        This might be useful, if you need to be aware of which section contains
        a certain property.
        """
        for section in config:
            for key in section:
                if __name__.lower() + '.' in key:
                    settings[__name__.__len__() + 1:] = section[key]

    def privmsg(self, server, channel, user, message):
        """
        Triggered whenever a message is received. Returning a string sends the
        string as a response to the user.
        """

    def botmsg(self, server, channel, message):
        """
        Triggered when the bot says something, including all responses
        generated by plugins.
        """

    def join(self, server, channel):
        """Triggered when a channel is joined."""

    def part(self, server, channel):
        """Triggered when a channel is left."""
 
    def modechanged(self, server, channel):
        """Triggered when a channel mode changes."""

    def topicchanged(self, server, channel, nick, oldtopic, newtopic):
        """Triggered whenever a channel's topic is changed."""

    def kicked(self, server, channel, reason):
        """Triggered when the bot is kicked from a channel."""
    
    def userjoin(self, server, channel, nick):
        """Triggered when a user joins a channel the bot is in."""

    def userpart(self, server, channel, nick, message):
        """Triggered when a user leaves a channel the bot is in."""

    def userkicked(self, server, channel, nick, reason):
        """Triggered when a user is kicked from a channel."""

    def userrenamed(self, server, channel, oldnick, newnick):
        """Triggered whenever a user changes his name."""

    def useraction(self, server, channel, nick, message):
        """
        Triggered whenever a user performs an action. Most clients use /me to
        allow users to do this.
        """

    def connect(self, server):
        """Triggered when the bot has connected to a server."""

    def disconnect(self, server):
        """Triggered when a bot has disconnected from a server."""

    def quit(self):
        """Last call to the plugin before bot termination."""

