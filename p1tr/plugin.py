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
        # Try current working directory
        module = __import__(os.path.join('plugins', plugin_name, plugin_name + '.py'))
    except ImportError:
        try:
            # Try P1tr home
            module = __import__(os.path.join(config['General']['home'], 'plugins', plugin_name, plugin_name + '.py'))
        except ImportError:
            # TODO: Try install location
            raise PluginError('Plugin not found.')
    
    # Create instance and check type.
    instance = getattr(getattr(module, plugin_name), plugin_name.capitalize())()
    if not (instance is Plugin):
        raise PluginError('Invalid plugin: Not derived from Plugin.')

    # Apply settings and return plugin instance.
    instance.apply_settings(config)
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

class require_op:
    """
    Commands with this decorator are only executed if the caller is op.
    """

    def __init__(self, func):
        self.func = func

    def __call__(self, *args):
        return self.func(*args)

class require_voice:
    """
    Commands with this decorator are only executed if the caller is op
    or has voice.
    """

    def __init__(self, func):
        self.fund = func

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
    You may give your plugin functionality by overriding the following methods:
    [TBD]
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
