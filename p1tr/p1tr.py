#!/usr/bin/env python3

import configparser
import os
import os.path
import sys
from oyoyo.client import IRCClient
from oyoyo.cmdhandler import DefaultCommandHandler
from oyoyo import helpers
from plugin import *

class BotError(Exception):
    """Raised on configuration- and non-plugin errors."""

class BotHandler(DefaultCommandHandler):

    plugins = dict()

    def load_config(self, path=None):
        """
        Attempts to load config from the specified path, or if not specified,
        from the file in the working directory called "config.cfg".

        Raises BotError if there is no config found.
        """
        self.config = configparser.ConfigParser()
        if path:
            if self.config.read(path) == []:
                raise BotError("No config at the specified path.")
        else:
            if self.config.read('config.cfg') == []:
                raise BotError("No config in the working directory.")
        # Set home, if available:
        try:
            self.home = self.config['General'].get('home')
            self.global_plugin_blacklist = self.config['General'].get(
                    'plugin_blacklist').split(',')
        except KeyError:
            self.home = ''
            self.global_plugin_blacklist = []

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
            paths.append(os.path.realpath(__file__))
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
                # Files and globally blacklisted plugins are skipped now.
                # Loading plugins, if a plugin with the same name has not been
                # loaded yet.
                try:
                    self.plugins[plugin_dir_name] = load_by_name(
                            plugin_dir_name, self.config)
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
                plugin.privmsg(self.client.host + ':' + str(self.client.port),
                    chan.decode('utf-8'), nick.decode('utf-8'),
                    msg.decode('utf-8')))

    def join(self, nick, chan):
        nick = nick.decode('utf-8')
        if nick.split('!')[0] == self.client.nick:
            self._for_each_plugin(lambda plugin:
                    plugin.join(self.client.host + ':' + str(self.client.port),
                        chan.decode('utf-8')))
        else:
            self._for_each_plugin(lambda plugin:
                    plugin.userjoin(self.client.host + ':' + str(self.client.port),
                        chan.decode('utf-8'), nick))
 
    def connected(self):
        self._for_each_plugin(lambda plugin:
                plugin.connect(self.client.host + ':' + str(self.client.port)))

    def quit(self, message):
        """Called on disconnect."""
        self._for_each_plugin(lambda plugin:
                plugin.disconnect(self.client.host + ':' + str(self.client.port),
                    message.decode('utf-8')))

    def exit(self):
        """Called on bot termination."""
        self._for_each_plugin(lambda plugin:
                plugin.quit())


def on_connect(client):
    client.command_handler.connected()
    helpers.join(client, '#p1tr-test')
    client.send('PRIVMSG', '#p1tr-test', ':Just talking...')

def main():
    client = IRCClient(BotHandler, host='irc.freenode.net', port=6667, nick='p1tr-test', connect_cb=on_connect)
    client.command_handler.load_config()
    client.command_handler.load_plugins()
    connection = client.connect()
    while True:
        try:
            next(connection) 
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
            break
    client.command_handler.exit()



if __name__ == '__main__':
    main()
