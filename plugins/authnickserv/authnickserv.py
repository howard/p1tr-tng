from p1tr.plugin import *
from oyoyo.helpers import ns, cs

@meta_plugin
class Authnickserv(AuthorizationProvider):
    """
    Provides authorization based on NickServ identities. The NickServ service
    enables users of an IRC network to register their nickname and secure it
    with a password.

    This provider's authorization mechanism requires users to be authenticated
    with NickServ in order to perform privileged operations. Additionally,
    certain criteria must be met, such as the user is operator of the channel
    or at least entitled to be operator according to ChanServ's ACCESS LIST.

    This authorization mechanism was developed for and tested on the freenode
    network. It may or may not work on other networks with the services NickServ
    and ChanServ.
    """

    """
    Each rank contains a dictionary with the nick as key, which has a list as
    value with a (next_queue, plugin, command, server, channel, nick, message)
    tuple as elements. If the notice listener detects a response from services
    concerning the nick, commands may be executed, depending on the response.
    If next_queue is set to another command queue, the tuple is forwarded to
    this queue for further processing.

    There is no queue for the master rank, since this can be checked instantly.
    """
    _command_queues = {
            'authenticated': {},
            'voice': {},
            'half-op': {},
            'op': {},
            'owner': {}
            }

    def _enqueue(self, queue_name, next_queue, plugin, command, server, channel,
            nick, message):
        """Adds a command to the appropriate queue for later processing."""
        user = nick.split('!')[0]
        if not user in self._command_queues[queue_name]:
            self._command_queues[queue_name][user] = []
        self._command_queues[queue_name][user].append(
                (next_queue, plugin, command, server, channel, nick, message))

    def _respond_denial(self, server, channel, nick):
        """Sends reponse to unauthorized users."""
        self.bot.client.send('PRIVMSG', channel, ':' + nick.split('!')[0] +
                ': You are not authorized to execute this command.')

    def authorize_master(self, server, channel, nick, message, plugin, cmd):
        """
        Master authorization requires nick to be authenticated with NickServ.
        Additionally, nick must be named master in the bot configuration.
        """
        if not self.master:
            self.master = self.bot.master
        user = nick.split('!')[0]
        if user == self.master:
            self._enqueue('authenticated', None, plugin, cmd, server, channel,
                    nick, message)
            ns(self.bot.client, 'ACC', user)
        else:
            self._respond_denial(server, channel, nick)

    def authorize_owner(self, server, channel, nick, message, plugin, cmd):
        """Nick must own the channel by having the founder flag."""

    def authorize_op(self, server, channel, nick, message, plugin, cmd):
        """
        Nick must be either OP in the channel, or able to become OP any time
        because of flags specified in ChanServ's ACCESS LIST.
        """

    def authorize_hop(self, server, channel, nick, message, plugin, cmd):
        """
        Nick must be either Half-OP in the channel, or able to become Half-OP
        any time because of flags specified in ChanServ's ACCESS LIST.
        """

    def authorize_voice(self, server, channel, nick, message, plugin, cmd):
        """
        Nick must have voice in the channel, or must be able to gain voice any
        time because of flags specified in ChanServ's ACCESS LIST.
        """
    
    def authorize_authenticated(self, server, channel, nick, message, plugin,
            cmd):
        """Nick must be authenticated with NickServ."""

    @command
    @require_master
    def auth(self, server, channel, nick, params):
        return 'Executed successfully.'

    def on_notice(self, server, channel, nick, message):
        if nick.startswith('NickServ!NickServ@services'):
            parts = message.split()
            user = parts[0]
            if not parts[1] == 'ACC': return # Response not of interest
            if not parts[2] == '3':
                # User is not authenticated. Privileged commands not available.
                for command in self._command_queues['authenticated'][user]:
                    self._respond_denial(command[3], command[4], command[5])
                self._command_queues['authenticated'][user] = [] # queues clear
                return
            # By now, it is confirmed that the user is authenticated.
            # If there is a next queue defined, transfer the command. Otherwise,
            # execute it.
            for command in self._command_queues['authenticated'][user]:
                if not command[0]: # No next queue
                    self.execute(command[3], command[4], command[5],
                            command[6].split(), command[1], command[2])
                else:
                    # Depending on the type of queue, certain information
                    # needs to be requested from the services. Launch request
                    # upon enqueueing.
                    self._enqueue(command[0], None, command[2], command[3],
                            command[4], command[5], command[6])
                    if command[0] == 'voice':
                        pass #TODO
                    elif command[0] == 'half-op':
                        pass #TODO
                    elif command[0] == 'op':
                        pass #TODO
                    elif command[0] == 'owner':
                        pass #TODO
            # Clear queue after executing/passing on commands.
            self._command_queues['authenticated'][user] = []
            return
        if nick.startswith('ChanServ!ChanServ@services'):
            pass
