from oyoyo.client import IRCClient
from oyoyo.client import IRCApp
from oyoyo.cmdhandler import DefaultCommandHandler
from oyoyo import helpers

import argparse
import configparser
import inspect
import logging
import os
import os.path
import sys
sys.path.insert(0, os.getcwd())

from p1tr.config import config_wizard, read_or_default, load_config
from p1tr.helpers import BotError
from p1tr.logwrap import *
from p1tr.plugin import *
from p1tr.test import run_tests


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

    def load_plugins(self):
        """
        Loads all plugins that are not blacklisted globally.
        Search order: extra_path -> $workingDir/plugins -> $p1trHome/plugins ->
            $installDir/plugins
        """
        for plugin_dir_name in discover_plugins(self.config):
            try:
                debug('Trying to load plugin ' + plugin_dir_name + '...')
                this_plugin = load_by_name(plugin_dir_name)
                # If this is a meta plugin, add the bot attribute:
                if hasattr(this_plugin, '__annotations__') and \
                        this_plugin.__annotations__['meta_plugin']:
                    debug(plugin_dir_name + ' is a meta plugin.')
                    this_plugin.bot = self
                # Load plugin-specific settings
                this_plugin.load_settings(self.config)
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
        if msg.decode().startswith('\x01ACTION'):
            self.action(nick, chan, msg)
            return
        # Regular PRIVMSG from here onwarts
        def _plugin_handler(plugin):
            ret_val = plugin.on_privmsg('%s:%d' % (self.client.host,
                self.client.port), chan.decode(), nick.decode(),
                msg.decode())
            if isinstance(ret_val, str) and len(ret_val) > 0:
                self.client.send('PRIVMSG', chan, ':' + ret_val)
        self._for_each_plugin(_plugin_handler)
        # Check for commands
        try:
            cmd = ''
            args = []
            msg = msg.decode()
            if chan.decode() == self.client.nick:
                respond_to = nick.decode().split('!')[0]
            else:
                respond_to = chan.decode()
            if msg.startswith(self.signal_character):
                parts = msg.replace(self.signal_character, '').split(' ')
                cmd = parts[0]
                args = parts[1:]
            elif msg.startswith(self.client.nick):
                parts = msg.replace(self.client.nick, '', 1).split(' ')
                cmd = parts[1]
                args = parts[2:]
            elif chan.decode() == self.client.nick: # In case of query
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
                        chan.decode(), nick.decode(),
                        msg, self.commands[cmd], cmd)
                return
            elif self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd, 'require_owner'):
                self.auth_provider.authorize_owner(server_str,
                        chan.decode(), nick.decode(),
                        msg, self.commands[cmd], cmd)
                return
            elif self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd, 'require_op'):
                self.auth_provider.authorize_op(server_str,
                        chan.decode(), nick.decode(),
                        msg, self.commands[cmd], cmd)
                return
            elif self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd, 'require_hop'):
                self.auth_provider.authorize_hop(server_str,
                        chan.decode(), nick.decode(),
                        msg, self.commands[cmd], cmd)
                return
            elif self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd, 'require_voice'):
                self.auth_provider.authorize_voice(server_str,
                        chan.decode(), nick.decode(),
                        msg, self.commands[cmd], cmd)
                return
            elif self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd,
                            'require_authenticated'):
                self.auth_provider.authorize_authenticated(server_str,
                        chan.decode(), nick.decode(),
                        msg, self.commands[cmd], cmd)
                return
            elif not self.auth_provider and \
                    has_annotation(self.commands[cmd], cmd, 'require_master'):
                # Even if no auth provider is available, restrict master
                # commands to users with a fitting nick. This is the least
                # we can do for security.
                if nick.decode().split('!')[0] != self.master: return
            # Not a privileged command. Handle as usual.
            ret_val = getattr(self.commands[cmd], cmd)(server_str,
                    chan.decode(), nick.decode(), args)
            # If text was returned, send it as a response.
            if isinstance(ret_val, str) or isinstance(ret_val, bytes):
                self.client.send('PRIVMSG', respond_to, ':' + ret_val)
                self._for_each_plugin(lambda plugin:
                        plugin.on_privmsg(server_str, respond_to,
                            self.client.nick, ret_val))
        except (ValueError, KeyError): pass

    def join(self, nick, chan):
        nick = nick.decode()
        if nick.split('!')[0] == self.client.nick:
            self._for_each_plugin(lambda plugin:
                    plugin.on_join(self.client.host + ':' + str(self.client.port),
                        chan.decode()))
        else:
            self._for_each_plugin(lambda plugin:
                    plugin.on_userjoin(self.client.host + ':' + str(self.client.port),
                        chan.decode(), nick))

    def connected(self):
        self._for_each_plugin(lambda plugin:
                plugin.on_connect(self.client.host + ':' + str(self.client.port)))

    def action(self, nick, chan, msg):
        """Called on actions (you usually do those with /me)"""
        self._for_each_plugin(lambda plugin:
                plugin.on_useraction(self.client.host + ':' +
                    str(self.client.port), chan.decode(),
                    nick.decode(),
                    ' '.join(msg.decode().split()[1:])))

    def notice(self, nick, chan, msg):
        """Usually issued by the server or services."""
        self._for_each_plugin(lambda plugin:
                plugin.on_notice(self.client.host + ':' +
                    str(self.client.port), chan.decode(),
                    nick.decode(), msg.decode()))

    def nick(self, oldnick, newnick):
        """Called when a user renames themselves."""
        self._for_each_plugin(lambda plugin:
                plugin.on_userrenamed(self.client.host + ':' +
                    str(self.client.port), oldnick.decode(),
                    newnick.decode()))

    def mode(self, nick, chan, msg):
        """Called on MODE responses."""
        self._for_each_plugin(lambda plugin:
                plugin.on_modechanged(self.client.host + ':' +
                    str(self.client.port), chan.decode(),
                    nick.decode(), msg.decode()))

    def quit(self, nick, message):
        """Called on disconnect."""
        self._for_each_plugin(lambda plugin:
                plugin.on_userquit(self.client.host + ':' + str(self.client.port),
                    nick.decode(), message.decode()))

    def exit(self):
        """Called on bot termination."""
        self._for_each_plugin(lambda plugin:
                plugin.on_quit())
        self._for_each_plugin(lambda plugin:
                plugin.close_all_storages())

    def __unhandled__(self, cmd, *args):
        """Unhandled commands go to this handler."""
        cmd = cmd.decode()
        if cmd == '353': # Channel member list
            channel = args[3].decode()
            # The member list may be spread across multiple messages
            if not channel in self.nicks:
                self.nicks[channel] = {}
            for nick in args[4].decode().split():
                if nick[0] in ('@', '%', '+'):
                    self.nicks[channel][nick[1:]] = nick[0]
                else:
                    self.nicks[channel][nick] = ''
        elif cmd == '366': # Channel member list fetching done.
            channel = args[2].decode()
            self._for_each_plugin(lambda plugin:
                    plugin.on_names(self.client.host + ':' +
                        str(self.client.port), channel,
                        self.nicks[channel]))
            self.nicks[channel] = {}
        elif cmd == '372': # MOTD
            self._for_each_plugin(lambda plugin:
                    plugin.on_motd(self.client.host + ':' +
                        str(self.client.port), args[2].decode()))
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
    argparser.add_argument('-m', '--mkconf',
            help='launches the configuration wizard',
            action='store_const', const=True, default=False)
    argparser.add_argument('-t', '--test',
            help='runs plugin test suites and exits afterwards. Requires valid \
configuration',
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
            config_loaded = True
        except BotError:
            error('No configuration file at the given path. Starting wizard...')
            config_path = config_wizard()

    loglevel = logging.ERROR
    set_loglevel(read_or_default(config, 'General', 'loglevel', logging.ERROR,
        lambda val: getattr(logging, val)))

    # Run tests if the flag is set
    if args.test:
        run_tests(config)
        return # Exit after tests

    application = IRCApp()
    application.sleep_time = read_or_default(config, 'General', 'sleeptime',
            0.2, lambda val: float(val))

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
                application.addClient(clients[section], autoreconnect=True)
            except (KeyError, configparser.NoOptionError): pass # Not a server.
            except ValueError as ve:
                info('Config section ' + section + ' will be ignored: ' + str(ve))

    info('Startup complete.')
    try:
        application.run()
    except KeyboardInterrupt:
        for client in clients:
            clients[client].command_handler.exit()
        application.stop()
        info('All clients terminated. Goodbye!')


if __name__ == '__main__':
    main()
