import argparse
import configparser
import inspect
import os
import os.path
import sys
sys.path.insert(0, os.getcwd())

from oyoyo.client import IRCClient
from oyoyo.cmdhandler import DefaultCommandHandler
from oyoyo import helpers
from p1tr.plugin import *

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


class BotError(Exception):
    """Raised on configuration- and non-plugin errors."""

class BotHandler(DefaultCommandHandler):

    plugins = dict()
    """
    The commands dictionary has the name of the command as key and
    plugin providing this command as value.
    """
    commands = dict()

    def load_config(self, config):
        self.config = config
        self.home = self.config.get('General', 'home') or ''
        self.global_plugin_blacklist = self.config.get('General',
                'plugin_blacklist').split(',') or []
        self.signal_character = self.config.get('General', 'signal_character') or '+'

    def load_plugins(self, extra_path=None):
        """
        Loads all plugins that are not blacklisted globally.
        Search order: extra_path -> $workingDir/plugins -> $p1trHome/plugins ->
            $installDir/plugins
        """
        if not self.config:
            raise BotError("Cannot load plugins if the configuration has not \
                    been loaded yet.")
        
        paths = ['plugins', os.path.join(self.home, 'plugins')]
        if (extra_path):
            paths.insert(0, extra_path)
        try:
            # plugins folder is in p1tr.py's parent directory.
            paths.append(os.path.join(
                os.path.split(
                    os.path.dirname(os.path.realpath(__file__)))[0], 'plugins'))
        except NameError: pass # __file__ is not defined in the python shell.
        paths = list(set(paths)) # Remove duplicates.

        for path in paths:
            plugin_dirs = []
            try: # Check if valid path.
                plugin_dirs = os.listdir(path)
            except OSError:
                continue
            # Consider all directories plugins
            for plugin_dir_name in plugin_dirs:
                plugin_dir = os.path.join(path, plugin_dir_name)
                if not os.path.isdir(plugin_dir): 
                    print(plugin_dir_name + ' is not directory.')
                    continue
                if plugin_dir_name in self.global_plugin_blacklist:
                    print(plugin_dir_name + ' is blacklisted.')
                    continue
                # Skip plugins if one with the same name has already been loaded
                if plugin_dir_name in self.plugins.keys():
                    print(plugin_dir_name + ' is a duplicate.')
                    continue
                # Files and globally blacklisted plugins are skipped now.
                # Loading plugins, if a plugin with the same name has not been
                # loaded yet.
                try:
                    this_plugin = load_by_name(plugin_dir_name, self.config)
                    # If this is a meta plugin, add the bot attribute:
                    if hasattr(this_plugin, '__annotations__') and \
                            this_plugin.__annotations__['meta_plugin']:
                        this_plugin.bot = self
                    # Scan for command methods:
                    for member in inspect.getmembers(this_plugin):
                        try:
                            if member[1].__annotations__['command'] == True:
                                self.commands[member[0]] = this_plugin
                                print('The plugin "' + plugin_dir_name +
                                        '" provides the command "' + member[0] + '".')
                        except (AttributeError, KeyError): pass # Not a command

                    self.plugins[plugin_dir_name] = this_plugin
                    print('Plugin ' + plugin_dir_name + ' was loaded.')
                except PluginError as pe:
                    print('Plugin ' + plugin_dir_name + 
                            ' could not be loaded: ' + str(pe))

    def _for_each_plugin(self, func):
        """
        Calls the given function for each plugin, with the plugin instance as a
        parameter.
        """
        for plugin_name in self.plugins:
            func(self.plugins[plugin_name])

    def privmsg(self, nick, chan, msg):
        self._for_each_plugin(lambda plugin:
                plugin.on_privmsg(self.client.host + ':' + str(self.client.port),
                    chan.decode('utf-8'), nick.decode('utf-8'),
                    msg.decode('utf-8')))
        # Check for commands
        try:
            cmd = ''
            args = []
            msg = msg.decode('utf-8')
            if chan.decode('utf-8') == self.client.nick:
                respond_to = nick.decode('utf-8').split('!')[0]
            else:
                respond_to = chan.decode('utf-8')
            if msg.startswith(self.signal_character):
                parts = msg.replace(self.signal_character, '').split(' ')
                cmd = parts[0]
                args = parts[1:]
            elif msg.startswith(self.client.nick):
                parts = msg.replace(self.client.nick, '', 1).split(' ')
                cmd = parts[1]
                args = parts[2:]
            elif chan.decode('utf-8') == self.client.nick: # In case of query
                parts = msg.split(' ')
                cmd = parts[0]
                args = parts[1:]
            else:
                return
            # Attempt to issue command, silently fail if this is not one.
            ret_val = getattr(self.commands[cmd], cmd)(self.client.host + ':' +
                    str(self.client.port), chan.decode('utf-8'),
                    nick.decode('utf-8'), args)
            # If text was returned, send it as a response.
            if isinstance(ret_val, str) or isinstance(ret_val, bytes):
                self.client.send('PRIVMSG', respond_to, ':' + ret_val)
        except (ValueError, KeyError): pass

    def join(self, nick, chan):
        nick = nick.decode('utf-8')
        if nick.split('!')[0] == self.client.nick:
            self._for_each_plugin(lambda plugin:
                    plugin.on_join(self.client.host + ':' + str(self.client.port),
                        chan.decode('utf-8')))
        else:
            self._for_each_plugin(lambda plugin:
                    plugin.on_userjoin(self.client.host + ':' + str(self.client.port),
                        chan.decode('utf-8'), nick))
 
    def connected(self):
        self._for_each_plugin(lambda plugin:
                plugin.on_connect(self.client.host + ':' + str(self.client.port)))

    def quit(self, message):
        """Called on disconnect."""
        self._for_each_plugin(lambda plugin:
                plugin.disconnect(self.client.host + ':' + str(self.client.port),
                    message.decode('utf-8')))

    def exit(self):
        """Called on bot termination."""
        self._for_each_plugin(lambda plugin:
                plugin.on_quit())


def on_connect(client):
    client.command_handler.connected()
    # Join channels listed in the configuration file.
    for section in client.command_handler.config.sections():
        if section.startswith(client.host) and '|' in section:
            client.send('JOIN', '#' + section.split('|')[1])
    # TODO: Auto-op if configured.


def main():
    argparser = argparse.ArgumentParser(description='P1tr TNG - IRC bot.')
    argparser.add_argument('-c', '--conf', help='path to configuration file',
            action='store', default='config.cfg')
    args = argparser.parse_args()

    clients = dict()
    connections = dict()

    config = load_config(args.conf)

    for section in config:
        if section != 'General' and not '|' in section:
            try:
                clients[section] = IRCClient(BotHandler,
                        host=section,
                        port=config.getint(section, 'port'),
                        nick=config.get(section, 'nick'),
                        connect_cb=on_connect)
                clients[section].command_handler.load_config(config)
                clients[section].command_handler.load_plugins()
                connections[section] = clients[section].connect()
            except (KeyError, configparser.NoOptionError): pass # Not a server.
            except ValueError as ve:
                print('Config error - section ' + section + ' will be ignored:')
                print(str(ve))

    while True:
        for client in clients:
            try:
                next(connections[client]) 
            except KeyboardInterrupt:
                break
    for client in clients:
        client.command_handler.exit()



if __name__ == '__main__':
    main()
