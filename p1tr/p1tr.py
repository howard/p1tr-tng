from oyoyo.client import IRCClient
from oyoyo.cmdhandler import DefaultCommandHandler
from oyoyo import helpers

import argparse
import configparser
import inspect
import logging
import os
import os.path
from string import ascii_lowercase
import sys
sys.path.insert(0, os.getcwd())

from p1tr.config import config_wizard, read_or_default, load_config
from p1tr.helpers import BotError
from p1tr.plugin import *
from p1tr.logwrap import *


class BotHandler(DefaultCommandHandler):

    plugins = dict()
    """
    The commands dictionary has the name of the command as key and
    plugin providing this command as value.
    """
    commands = dict()

    """
    One plugin should serve as the authorization provider. The first
    non-blacklisted plugin is used.
    """
    auth_provider = None

    """Temporary storage for loading nicklists for channels."""
    nicks = {}

    def load_config(self, config):
        self.config = config
        self.home = self.config.get('General', 'home') or ''
        info('Bot home: ' + self.home)
        self.global_plugin_blacklist = self.config.get('General',
                'plugin_blacklist').split(',') or []
        info('Global plugin blacklist: ' + str(self.global_plugin_blacklist))
        self.signal_character = self.config.get('General', 'signal_character') \
                or '+'
        info('Signal character: ' + self.signal_character)
        self.master = read_or_default(self.config, self.client.host, 'master',
                '')

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
        debug('Plugin directories: ' + str(paths))

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
                if plugin_dir_name in self.global_plugin_blacklist:
                    debug(plugin_dir_name + ' is blacklisted globally.')
                    continue
                # Skip plugins if one with the same name has already been loaded
                if plugin_dir_name in self.plugins.keys():
                    debug(plugin_dir_name + ' has been loaded before. Skipping.')
                    continue
                # Files and globally blacklisted plugins are skipped now.
                # Loading plugins, if a plugin with the same name has not been
                # loaded yet.
                try:
                    debug('Trying to load plugin ' + plugin_dir_name + '...')
                    this_plugin = load_by_name(plugin_dir_name, self.config)
                    # If this is a meta plugin, add the bot attribute:
                    if hasattr(this_plugin, '__annotations__') and \
                            this_plugin.__annotations__['meta_plugin']:
                        debug(plugin_dir_name + ' is a meta plugin.')
                        this_plugin.bot = self
                    # Register as authorization provider, if possible:
                    if not self.auth_provider and \
                            isinstance(this_plugin, AuthorizationProvider):
                        self.auth_provider = this_plugin
                        info('Authorization provider: ' + plugin_dir_name)
                    # Set data storage path:
                    this_plugin.data_path = os.path.join(self.home, 'data',
                            plugin_dir_name)
                    # Scan for command methods:
                    for member in inspect.getmembers(this_plugin):
                        try:
                            if member[1].__annotations__['command'] == True:
                                self.commands[member[0]] = this_plugin
                                debug('Registered command ' + member[0] +
                                        ' for plugin ' + plugin_dir_name)
                        except (AttributeError, KeyError): pass # Not a command

                    self.plugins[plugin_dir_name] = this_plugin
                    info('Plugin ' + plugin_dir_name + ' was loaded.')
                except PluginError as pe:
                    error('Plugin ' + plugin_dir_name + 
                            ' could not be loaded: ' + str(pe))

    def _for_each_plugin(self, func):
        """
        Calls the given function for each plugin, with the plugin instance as a
        parameter.
        """
        for plugin_name in self.plugins:
            func(self.plugins[plugin_name])

    def privmsg(self, nick, chan, msg):
        # Check if this is actually a PRIVMSG, not an action.
        if msg.decode('utf-8').startswith('\x01ACTION'):
            self.action(nick, chan, msg)
            return
        # Regular PRIVMSG from here onwarts
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
            if cmd not in self.commands: return # Not a command
            # If command requires authorization, delegate execution to the
            # authorization provider, if available.
            server_str = self.client.host + ':' + str(self.client.port)
            if self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd, 'require_master'):
                self.auth_provider.authorize_master(server_str,
                        chan.decode('utf-8'), nick.decode('utf-8'),
                        msg, self.commands[cmd], cmd)
                return
            elif self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd, 'require_owner'):
                self.auth_provider.authorize_owner(server_str,
                        chan.decode('utf-8'), nick.decode('utf-8'),
                        msg, self.commands[cmd], cmd)
                return
            elif self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd, 'require_op'):
                self.auth_provider.authorize_op(server_str,
                        chan.decode('utf-8'), nick.decode('utf-8'),
                        msg, self.commands[cmd], cmd)
                return
            elif self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd, 'require_hop'):
                self.auth_provider.authorize_hop(server_str,
                        chan.decode('utf-8'), nick.decode('utf-8'),
                        msg, self.commands[cmd], cmd)
                return
            elif self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd, 'require_voice'):
                self.auth_provider.authorize_voice(server_str,
                        chan.decode('utf-8'), nick.decode('utf-8'),
                        msg, self.commands[cmd], cmd)
                return
            elif self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd,
                            'require_authenticated'):
                self.auth_provider.authorize_authenticated(server_str,
                        chan.decode('utf-8'), nick.decode('utf-8'),
                        msg, self.commands[cmd], cmd)
                return
            elif not self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd, 'require_master'):
                # Even if no auth provider is available, restrict master
                # commands to users with a fitting nick. This is the least
                # we can do for security.
                if nick.decode('utf-8').split('!')[0] != self.master: return
            # Not a privileged command. Handle as usual.
            ret_val = getattr(self.commands[cmd], cmd)(server_str,
                    chan.decode('utf-8'), nick.decode('utf-8'), args)
            # If text was returned, send it as a response.
            if isinstance(ret_val, str) or isinstance(ret_val, bytes):
                self.client.send('PRIVMSG', respond_to, ':' + ret_val)
                self._for_each_plugin(lambda plugin:
                        plugin.on_privmsg(server_str, respond_to,
                            self.client.nick, ret_val))
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

    def action(self, nick, chan, msg):
        """Called on actions (you usually do those with /me)"""
        self._for_each_plugin(lambda plugin:
                plugin.on_useraction(self.client.host + ':' +
                    str(self.client.port), chan.decode('utf-8'),
                    nick.decode('utf-8'),
                    ' '.join(msg.decode('utf-8').split()[1:])))

    def notice(self, nick, chan, msg):
        """Usually issued by the server or services."""
        self._for_each_plugin(lambda plugin:
                plugin.on_notice(self.client.host + ':' +
                    str(self.client.port), chan.decode('utf-8'),
                    nick.decode('utf-8'), msg.decode('utf-8')))

    def nick(self, oldnick, newnick):
        """Called when a user renames themselves."""
        self._for_each_plugin(lambda plugin:
                plugin.on_userrenamed(self.client.host + ':' +
                    str(self.client.port), oldnick.decode('utf-8'),
                    newnick.decode('utf-8')))

    def mode(self, nick, chan, msg):
        """Called on MODE responses."""
        self._for_each_plugin(lambda plugin:
                plugin.on_modechanged(self.client.host + ':' +
                    str(self.client.port), chan.decode('utf-8'),
                    nick.decode('utf-8'), msg.decode('utf-8')))

    def quit(self, message):
        """Called on disconnect."""
        self._for_each_plugin(lambda plugin:
                plugin.disconnect(self.client.host + ':' + str(self.client.port),
                    message.decode('utf-8')))

    def exit(self):
        """Called on bot termination."""
        self._for_each_plugin(lambda plugin:
                plugin.on_quit())
        self._for_each_plugin(lambda plugin:
                plugin.close_all_storages())
        
    def __unhandled__(self, cmd, *args):
        """Unhandled commands go to this handler."""
        cmd = cmd.decode('utf-8')
        if cmd == '353': # Channel member list
            channel = args[3].decode('utf-8')
            # The member list may be spread across multiple messages
            if not channel in self.nicks:
                self.nicks[channel] = {}
            for nick in args[4].decode('utf-8').split():
                if nick[0] in ('@', '%', '+'):
                    self.nicks[channel][nick[1:]] = nick[0]
                else:
                    self.nicks[channel][nick] = ''
        elif cmd == '366': # Channel member list fetching done.
            channel = args[2].decode('utf-8')
            self._for_each_plugin(lambda plugin:
                    plugin.on_names(self.client.host + ':' +
                        str(self.client.port), channel,
                        self.nicks[channel]))
            self.nicks[channel] = {}
        else:
            debug('Unknown command: [' + cmd + '] ' + str(args),
                    server=self.client.host)  


def on_connect(client):
    client.command_handler.connected()
    # Join channels listed in the configuration file.
    debug('Joining startup channels...')
    for section in client.command_handler.config.sections():
        if section.startswith(client.host) and '|' in section:
            client.send('JOIN', '#' + section.split('|')[1])
    # TODO: Auto-op if configured.


def main():
    argparser = argparse.ArgumentParser(description='P1tr TNG - IRC bot.')
    argparser.add_argument('-c', '--conf', help='path to configuration file',
            action='store', default='config.cfg')
    argparser.add_argument('-m', '--mkconf', help='launches the configuration wizard',
            action='store_const', const=True, default=False)
    args = argparser.parse_args()

    clients = dict()
    connections = dict()
    config_path = args.conf

    # Launch configuration wizard, if desired, before bot launch
    if args.mkconf:
        config_path = config_wizard()

    config_loaded = False
    while not config_loaded:
        try:
            config = load_config(config_path)
        except BotError:
            error('No configuration file at the given path. Starting wizard...')
            config_path = config_wizard()
    
    loglevel = logging.ERROR
    set_loglevel(read_or_default(config, 'General', 'loglevel', logging.ERROR,
        lambda val: getattr(logging, val)))

    info('Connecting to servers...')
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
                info('Config section ' + section + ' will be ignored: ' + str(ve))

    info('Startup complete.')
    running = True
    try:
        while running:
            for client in clients:
                next(connections[client]) 
    except KeyboardInterrupt:
        running = False
    for client in clients:
        clients[client].command_handler.exit()
    info('All clients terminated. Goodbye!')



if __name__ == '__main__':
    main()
