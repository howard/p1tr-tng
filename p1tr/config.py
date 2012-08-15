"""P1tr configuration wizard."""

import configparser
import os.path
from p1tr.helpers import boolify, BotError, pretty_list
from p1tr.logwrap import info

def prompt(description, default, vals=[]):
    """
    Prompts for input. If the user just presses enter, default is assumed. If
    the possible values are defined in the optional third parameter, the entered
    value must be from that list, or the user will be prompted again.
    """
    success = False
    if len(vals) > 0:
        if not default in vals:
            vals.append(default)
        vals.sort()
        prompt_str = '%s (%s) [%s] ' % (description,
            pretty_list(vals), default)
    else:
        prompt_str = '%s [%s] ' % (description, default)
    while not success:
        value = input(prompt_str)
        if value in vals:
            success = True
        elif len(value) < 1: # Assume default
            value = default
            success = True
        elif len(vals) < 1: # Value entered, no restrictions defined
            success = True
        else:
            print('Invalid value. Must be one of the following: ' + str(vals))
    return value

def _bool_to_config(boolean):
    """
    ConfigParser can only write strings. Therefore, convert True and False to
    yes and no, respectively.
    """
    if boolean:
        return 'yes'
    else:
        return 'no'

def _write_general(config, home, loglevel, background, plugin_blacklist,
        signal_char):
    """Adds a general section to a given ConfigParser object."""
    config['General'] = {
            'home': home,
            'loglevel': loglevel,
            'background': _bool_to_config(background),
            'plugin_blacklist': plugin_blacklist,
            'signal_character': signal_char
    }

def _write_server(config, host, port, nick, nick_password, master,
        server_password, plugin_blacklist):
    """
    Modifies a ConfigParser object to contain a proper server section with the
    given values set.
    """
    config[host] = {
            'host': host,
            'port': port,
            'nick': nick,
            'nick_password': nick_password,
            'master': master,
            'server_password': server_password,
            'plugin_blacklist': plugin_blacklist
    }

def _write_channel(config, host, channel, enable_logging,
        plugin_blacklist):
    """
    Modifies a ConfigParser object to contain a proper channel section with the
    given values set.
    """
    config['%s|%s' % (host, channel[1:])] = {
            'logger.log': _bool_to_config(enable_logging),
            'plugin_blacklist': plugin_blacklist
    }


def config_wizard():
    """Interactive configuration tool; returns path to generated config file."""
    config = configparser.ConfigParser()
    print('General configuration')
    print('=====================')
    home = prompt("P1tr's home directory. The contents of $home/plugins are \
loaded and treated as plugins. $home/log is the storage location for log \
files. $home/data contains the plugins' persistent storage files.", '.')
    loglevel = prompt('Loglevel - the lowest non-ignored log message severity:',
            'INFO', ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    background = boolify(prompt('Run bot in background?', 'no'))
    plugin_blacklist = prompt('Plugin blacklist - names of plugins, separated \
by spaces, or empty:', '')
    signal_char = prompt('Signal character - Commands must begin with \
this character (or the user addressing the bot):', '!')
    _write_general(config, home, loglevel, background, plugin_blacklist,
            signal_char)

    print('\nServer Configuration')
    print('===================')
    one_more_server = True
    while one_more_server: # Allow adding multiple servers
        host = prompt('Host:', 'irc.freenode.net')
        port = prompt('Port:', '6667')
        nick = prompt('Bot nickname:', 'P1tr')
        nick_password = prompt('NickServ password for nickname (if available):',
                '')
        master = prompt('Master nickname:', 'yourNick')
        server_password = prompt('Server password (if any):', '')
        plugin_blacklist = prompt('Plugin blacklist - names of plugins, \
separated by spaces, or empty:', '')
        _write_server(config, host, port, nick, nick_password, master,
            server_password, plugin_blacklist)
        one_more_channel = True
        while one_more_channel: # Allow adding multiple channels per server
            channel = prompt('Channel name (starts with #):', '#p1tr')
            enable_logging = boolify(prompt('Log conversations?', 'yes'))
            plugin_blacklist = prompt('Plugin blacklist - names of \
plugins, separated by spaces, or empty:', '')
            _write_channel(config, host, channel, enable_logging,
                plugin_blacklist)
            one_more_channel = boolify(prompt('Add another channel?', 'no'))
        one_more_server = boolify(prompt('Add another server?', 'no'))

    print()
    saved_successfully = False
    while not saved_successfully:
        try:
            path = prompt('Save configuration file to:', 'config.cfg')
            with open(path, 'w') as out_file:
                config.write(out_file)
            saved_successfully = True
        except IOError:
            print('Unable to write file. Choose a different path.')
    return path


def read_or_default(config, section, key, default,
        manipulator=lambda val: val):
    """
    Tries to read a certain key from a certain config section. If either section
    or key cannot be found, the provided default value is returned.
    Optionally, a multiplicator can be provided to manipulate the config value
    before returning. If this manipulator fails, the default value is returned.
    """
    try:
        return manipulator(config.get(section, key))
    except:
        info('Key ' + key + ' not found in config section ' + section + '.')
        return default


def load_config(path=None):
    """
    Attempts to load config from the specified path, or if not specified,
    from the file in the working directory called "config.cfg".

    Raises BotError if there is no config found.
    """
    config = configparser.ConfigParser()
    if path:
        if config.read(path) == []:
            raise BotError("No config at the specified path.")
    else:
        if config.read('config.cfg') == []:
            raise BotError("No config in the working directory.")
    return config


