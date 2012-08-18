"""
Plugin base class and related utilities.
"""
import glob
import os.path
import shelve
from string import ascii_lowercase
from p1tr.config import read_or_default
from p1tr.helpers import pretty_list
from p1tr.logwrap import *

def discover_plugins(config):
    """
    Finds the names of possible plugins, which can be found in the search
    directories. Locations are searched in the following order:
    Current working directory -> Bot home -> Bot install location
    Note that for each of the locations above, the "plugins" sub-directory is
    searched.
    Also note that when running P1tr standalone (not easy_install3'd), the
    bot install location is where you put the bot's Python files.
    If a plugin with the same name is found in two different locations, the one
    found first has precedence.
    This function does not load the plugins, just deliver a list of names!
    """
    plugin_names = [] # Results
    if not config: # Config is essential to find all possible plugin dirs
        raise BotError("Cannot load plugins if the configuration has not \
                been loaded yet.")
    home = read_or_default(config, 'General', 'home', '.')
    global_plugin_blacklist = read_or_default(config, 'General',
            'plugin_blacklist', [], lambda val: val.split())

    # Assemble search paths. If you need to add custom ones, just add them to
    # the path list below. The rest of the function can remain unchanged.
    paths = ['plugins', os.path.join(home, 'plugins')]
    try:
        # plugins folder is in p1tr.py's parent directory.
        paths.append(os.path.join(
            os.path.split(
                os.path.dirname(os.path.realpath(__main__.__file__)))[0],
            'plugins'))
    except NameError: # __file__ is not defined in the python shell.
        warning('Cannot determine install directory. Ignoring.')
    paths = list(set(paths)) # Remove duplicates.
    debug('Plugin directories: %s' % pretty_list(paths))

    # Search vor possible plugins
    for path in paths:
        plugin_dirs = []
        try: # Check if valid path.
            plugin_dirs = os.listdir(path)
        except OSError:
            debug(path + ' is not a valid directory.')
            continue
        # Consider all directories plugins as long as they start with
        # a character.
        for plugin_dir_name in plugin_dirs:
            plugin_dir = os.path.join(path, plugin_dir_name)
            if not plugin_dir_name.lower()[0] in ascii_lowercase:
                debug(plugin_dir + ' is not a plugin directory.')
                continue
            if not os.path.isdir(plugin_dir):
                debug(plugin_dir + ' is not a plugin directory.')
                continue
            if plugin_dir_name in global_plugin_blacklist:
                debug(plugin_dir_name + ' is blacklisted globally.')
                continue
            # Skip plugins if one with the same name has already been loaded
            if plugin_dir_name in plugin_names:
                debug(plugin_dir_name + ' has been found before. Skipping.')
                continue
            # It passed all tests. It's most likely a plugin.
            plugin_names.append(plugin_dir_name)
    plugin_names.sort()
    return plugin_names


def load_by_name(plugin_name):
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
    4. The instance of the plugin is returned.
    If any step fails, a PluginError exception is thrown.

    The parameter config should be an instance of ConfigParser, which has
    already parsed the config file.
    """
    try:
        module = __import__('plugins.' + plugin_name + '.' + plugin_name)
    except ImportError:
        raise PluginError('Plugin "' + plugin_name + '" not found.')

    # Create instance and check type.
    instance = getattr(getattr(getattr(module, plugin_name), plugin_name),
            plugin_name.capitalize())()
    if not isinstance(instance, Plugin):
        raise PluginError('Invalid plugin: Not derived from Plugin.')
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

def require_authenticated(func):
    return _add_annotation(func, 'require_authenticated', True)

def has_annotation(plugin, command, annotation):
    """Checks if an annotation is set for a given command in a given plugin."""
    if not hasattr(plugin, command): return false
    if not hasattr(getattr(plugin, command), '__annotations__'): return false
    return annotation in getattr(plugin, command).__annotations__


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

    """Registry of all open storages."""
    _storages = {}

    """
    Plugin-specific settings; meant to be accessible to the plugin container.
    """
    _settings = dict()

    """
    Path at which the plugin may store data. Usually in the data/pluginName
    directory under the bot home directory. This property is to be set at plugin
    instantiation. Otherwise, the current working directory will be used as a
    fallback.
    """
    data_path = ''

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

    def load_storage(self, identifier):
        """
        Persistent storage mechanism for P1tr plugins. Calling this method
        returns a dictionary-like key-value-storage, backed by Python's shelve
        module. Pretty much anything can be serialized using this mechanism. For
        details, refer to the documentation of the shelve module.

        The pickle protocol version 3 is used, which was introduced with Python
        3 and is not backward compatible.

        The file behind this storage instance is stored in the file at
        $home/data/$plugin/$identifier.db, whereas $home is the bot home
        directory, $plugin the name of this plugin, and $identifier the
        parameter supplied at the method call. A plugin can have an arbitrary
        number of storage files.

        You can explicitly save the storage by calling the save_storage method.
        All storages are automatically saved and closed on termination of the
        plugin.
        """
        path = os.path.join(self.data_path, identifier)
        try:
            storage = shelve.open(path, protocol=3, writeback=True)
            self._storages[identifier] = storage
            debug('Loaded storage at: ' + path)
            return storage
        except Exception as e:
            error('Unable to load storage file at ' + path + ':',
                    plugin=self.__class__.__name__.lower())
            error(str(e))
            raise

    def save_storage(self, identifier=None, storage=None):
        """
        Saves storage data. Identify the storage you want to save either by
        supplying the identifier or the storage object itself. Are both
        provided, the identifier will be prefered over the storage object.
        """
        if identifier:
            if not identifier in self._storages:
                error('Storage with the identifier "' + identifier +
                        '" not found.', plugin=self.__class__.__name__.lower())
            else:
                self._storages[identifier].sync()
                debug('Storage "' + identifier + '" saved.',
                        plugin=self.__class__.__name__.lower())
        elif storage:
            debug('Storage "' + str(storage) + '" saved.',
                     plugin=self.__class__.__name__.lower())
        else:
            raise ValueError('Specify identifier or storage for saving.')

    def close_storage(self, identifier=None, storage=None):
        """
        Closes a storage. Identify the storage you want to close either by
        supplying the identifier or the storage object itself. Are both
        provided, the identifier will be prefered over the storage object.
        """
        if identifier:
            if not identifier in self._storages:
                error('Storage with the identifier "' + identifier +
                        '" not found.', plugin=self.__class__.__name__.lower())
            else:
                self._storages[identifier].close()
                del self._storages[identifier]
                debug('Storage "' + identifier + '" closed.',
                        plugin=self.__class__.__name__.lower())
        elif storage:
            storage.close()
            # In case the storage is referenced in self._storages, remove it to
            # avoid redundant closing on plugin termination.
            identifier = [key for key, value in self._storages.iteritems()
                    if value == storage]
            if len(identifier) > 0:
                del self._storages[identifier[0]]
            debug('Storage "' + str(storage) + '" closed.',
                    plugin=self.__class__.__name__.lower())
        else:
            raise ValueError('Specify identifier or storage for closing.')

    def close_all_storages(self):
        """
        This method is automatically called on plugin termination by the plugin
        container (the bot). It is not intended for being called or overridden
        by the plugin itself.
        """
        for storage in self._storages:
            self._storages[storage].sync()
            self._storages[storage].close()

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

    def on_motd(self, server, message):
        """Triggered when the server sends a MOTD message."""

    def on_notice(self, server, chanel, nick, message):
        """Notices are usually issued by the server or services."""

    def on_join(self, server, channel):
        """Triggered when a channel is joined."""

    def on_part(self, server, channel):
        """Triggered when a channel is left."""

    def on_modechanged(self, server, channel, nick, message):
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

    def on_userrenamed(self, server, oldnick, newnick):
        """Triggered whenever a user changes his name."""

    def on_useraction(self, server, channel, nick, message):
        """
        Triggered whenever a user performs an action. Most clients use /me to
        allow users to do this.
        """

    def on_userquit(self, server, nick, message):
        """Triggered whenever a user disconnects from the server."""

    def on_names(self, server, channel, namelist):
        """Triggered when channel member list is received."""

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

    The available ranks are:
    Default < Authenticated < Voice < Half-OP < OP < Channel Owner < Master
    Privileges of inferior ranks are included in superior ranks. All privileged
    commands, which means all commands requiring ranks starting at
    Authenticated, go through the authorization provider in use. Execution of
    the command is delegated to the provider, to be performed upon successful
    authorization.

    Keep in mind that the rank inclusion of inferior ranks in superior ranks
    must be implemented by the authorization provider.
    """

    master = None

    def execute(self, server, channel, nick, message, plugin, cmd):
        """Executes a plugin command."""
        ret_val = getattr(plugin, cmd)(server, channel, nick,
                message.split()[1:])
        if isinstance(ret_val, str) or isinstance(ret_val, bytes):
            self.bot.client.send('PRIVMSG', channel, ':' + ret_val)

    def authorize_master(self, server, channel, nick, message, plugin, cmd):
        """
        Bot master authorization. A simple implementation might be checking the
        nick. To be implemented by the actual authorization providers.
        """
        critical('Master authorizer not implemented!')
        self.execute(server, channel, nick, message, plugin, cmd)

    def authorize_owner(self, server, channel, nick, message, plugin, cmd)  :
        """
        Owner of the channel. Usually a unique rank, but depends on the
        authorization provider, which is to be implemented.
        """
        critical('Owner authorizer not implemented.')
        self.execute(server, channel, nick, message, plugin, cmd)

    def authorize_op(self, server, channel, nick, message, plugin, cmd) :
        """
        Rank of a channel-wide authority. Not necessarily bound to the IRC
        protocol's OP status. To be implemented by the actual authorization
        providers.
        """
        critical('OP authorizer not implemented!')
        self.execute(server, channel, nick, message, plugin, cmd)

    def authorize_hop(self, server, channel, nick, message, plugin, cmd):
        """
        Half-OP. Ranked above voice. To be implemented by the
        actual authorization providers.
        """
        critical('Half-OP authorizer not implemented!')
        self.execute(server, channel, nick, message, plugin, cmd)

    def authorize_voice(self, server, channel, nick, message, plugin, cmd):
        """
        Privileged user, but usually without administrative abilities. To be
        implemented by the actual authorization providers.
        """
        critical('Voice authorizer not implemented!')
        self.execute(server, channel, nick, message, plugin, cmd)

    def authorize_authenticated(self, server, channel, nick, message, plugin,
            cmd):
        """
        Used for requiring the nick to be authenticated with the bot. To be
        implemented by the actual authorization providers.
        """
        critical('Authenticated authorizer not implemented!')
        self.execute(server, channel, nick, message, plugin, cmd)
