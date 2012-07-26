"""
Plugin base class and related utilities.
"""
import glob
import os.path
from p1tr.logwrap import warning, critical

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
def _add_annotation(decoratable, key, value):
    """Adds value at key in decoratable's __annotations__ attribute."""
    try:
        decoratable.__annotations__[key] = value
    except AttributeError:
        decoratable.__annotations__ = {key: value}
    return decoratable

def meta_plugin(a_class):
    """
    Plugin classes decorated with this item receive a special attribute after
    contruction of type p1tr.p1tr.BotHandler as self.bot, which gives full
    access to the bot (enabling raw operations on the IRC protocol), and to
    all plugin instances. Use with caution and only if absolutely necessary.
    You could break a lot.
    """
    return _add_annotation(a_class, 'meta_plugin', True)

def command(func):
    return _add_annotation(func, 'command', True)

def require_master(func):
    return _add_annotation(func, 'require_master', True)

def require_owner(func):
    return _add_annotation(func, 'require_owner', True)

def require_op(func):
    return _add_annotation(func, 'require_op', True)

def require_voice(func):
    return _add_annotation(func, 'require_voice', True)

    
# Some utility functions
def clean_string(string):
    """
    Converts whitespace (includes newlines etc.) to single spaces. Useful to
    avoid problems with the IRC protocol, which treats newlines, for example,
    as message terminator.
    """
    if isinstance(string, bytes):
        string = string.decode('utf-8')
    return ' '.join(string.split())


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

    def on_privmsg(self, server, channel, user, message):
        """
        Triggered whenever a message is received. Returning a string sends the
        string as a response to the user.
        """

    def on_botmsg(self, server, channel, message):
        """
        Triggered when the bot says something, including all responses
        generated by plugins.
        """

    def on_notice(self, server, chanel, nick, message):
        """Notices are usually issued by the server or services."""

    def on_join(self, server, channel):
        """Triggered when a channel is joined."""

    def on_part(self, server, channel):
        """Triggered when a channel is left."""
 
    def on_modechanged(self, server, channel):
        """Triggered when a channel mode changes."""

    def on_topicchanged(self, server, channel, nick, oldtopic, newtopic):
        """Triggered whenever a channel's topic is changed."""

    def on_kicked(self, server, channel, reason):
        """Triggered when the bot is kicked from a channel."""
    
    def on_userjoin(self, server, channel, nick):
        """Triggered when a user joins a channel the bot is in."""

    def on_userpart(self, server, channel, nick, message):
        """Triggered when a user leaves a channel the bot is in."""

    def on_userkicked(self, server, channel, nick, reason):
        """Triggered when a user is kicked from a channel."""

    def on_userrenamed(self, server, channel, oldnick, newnick):
        """Triggered whenever a user changes his name."""

    def on_useraction(self, server, channel, nick, message):
        """
        Triggered whenever a user performs an action. Most clients use /me to
        allow users to do this.
        """

    def on_connect(self, server):
        """Triggered when the bot has connected to a server."""

    def on_disconnect(self, server):
        """Triggered when a bot has disconnected from a server."""

    def on_quit(self):
        """
        Last call to the plugin before bot termination. May also be called
        before reloading the plugin.
        """

class AuthorizationProvider(Plugin):
    """
    Template for authorization-providing plugins. Provides common functionality,
    such as a custom settings loader, which fetches the bot master from the
    config file.

    One thing to note about the authorization system: The authorization
    methods are passed the plugin and the command name. It's up to the
    implementation to execute the command. This permits deferred command
    processing.
    """

    def load_settings(self, config):
        try:
            self.master = config.get('General', 'master')
        except:
            warning('No bot master specified in config file.')
    
    def authorize_master(self, server, channel, nick, message, plugin, cmd):
        """
        Bot master authorization. A simple implementation might be checking the
        nick. To be implemented by the actual authorization providers.
        """
        critical('Master authorizer not implemented!')

    def authorize_owner(self, server, channel, nick, message, plugin, cmd)  :
        """
        Owner of the channel. Usually a unique rank, but depends on the
        authorization provider, which is to be implemented.
        """
        critical('Owner authorizer not implemented.')

    def authorize_op(self, server, channel, nick, message, plugin, cmd) :
        """
        Rank of a channel-wide authority. Not necessarily bound to the IRC
        protocol's OP status. To be implemented by the actual authorization
        providers.
        """
        critical('OP authorizer not implemented!')

    def authorize_hop(self, server, channel, nick, message, plugin, cmd):
        """
        Half-OP. Ranked above voice. To be implemented by the 
        actual authorization providers.
        """
        critical('Half-OP authorizer not implemented!')

    def authorize_voice(self, server, channel, nick, message, plugin, cmd):
        """
        Privileged user, but usually without administrative abilities. To be
        implemented by the actual authorization providers.
        """
        critical('Voice authorizer not implemented!')
