from collections import namedtuple
import datetime
import hashlib
import random
import string
from p1tr.plugin import *
from p1tr.helpers import *
from p1tr.logwrap import *

def User(rank, registered_at, authenticated_at, password_hash):
    """Generates a user data structure."""
    return {'rank': rank, 'registered_at': registered_at,
            'authenticated_at': authenticated_at, 'password_hash': None }

def hash_password(username, password):
    """
    Creates hex digest of SHA512 hash, which is used for registration and
    authentication.
    """
    m = hashlib.sha512()
    m.update(username.encode('utf-8'))
    m.update(password.encode('utf-8'))
    return m.hexdigest()

def generate_password():
    """
    Randomly generates a password for reset. Inspired by Ignacio Vazquez-Abrams:
    http://stackoverflow.com/questions/2257441/python-random-string-generation-
    with-upper-case-letters-and-digits
    """
    return ''.join(
            random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits)
            for i in range(8))

@meta_plugin
class Authdefault(AuthorizationProvider):
    """
    Provides self-contained authorization; users are managed by P1tr himself.
    Users are unprivileged by default. Using the authenticate command, they
    gain the rank "authenticated". If the user has been assigned a higher rank
    by the master, this rank is in effect then. Note that all ranks are
    server-wide.
    """

    def load_settings(self, config):
        """
        Check if there is a new master. If yes, make an entry for them in
        storage and set the password to the nickname. Remind the user whenever
        they are active that they should change the password via query.
        If there was a previous master, remove their privileges.
        """
        user = config.get(self.bot.client.host, 'master')
        # Replace old master
        if ':master' in self.users and user != self.users[':master']:
            self.users[self.users[':master']]['rank'] = 'none'
        if not user in self.users:
            self.users[user] = User('master', datetime.datetime.now(), None,
                    hash_password(user, user))
        if not ':master' in self.users or self.users[':master'] != user:
            self.users[':master'] = user
            self.users[':new_master'] = True

    def __init__(self):
        self.users = self.load_storage('user_data')
        # De-authenticate all users
        for user in self.users:
            if user[0] != ':':
                self.users[user]['authenticated_at'] = None

    @command
    @require_master
    def assign_rank(self, server, channel, nick, params):
        """
        Usage: assign_rank NICK none|voice|half-op|op|owner - assigns the rank
        to the specified user.
        """
        if len(params) < 2 or \
                not params[1] in ('none', 'voice', 'half-op', 'op', 'owner'):
            return clean_string(self.assign_rank.__doc__)
        user = params[0]
        if not user in self.users:
            return '%s is not registered.'
        else:
            info('The rank of %s was changed to %s.' % (user, params[1]),
                    plugin='authdefault')
            self.users[user].rank = params[1]
            return 'The rank of %s was changed to %s.' % (user, params[1])

    @command
    def authenticate(self, server, channel, nick, params):
        """
        Usage: authenticate PASSWORD - if the password is correct, you will be
        authenticated and perform acts according to your rank. It is highly
        suggested to use this command from within a query.
        """
        if len(params) < 1:
            return clean_string(self.authenticate.__doc__)
        user = nick.split('!')[0]
        password = ' '.join(params)
        if not user in self.users:
            return '%s: You are not registered yet.' % user
        if self.users[user]['authenticated_at']:
            return '%s: You are already authenticated.' % user
        if hash_password(user, password) == self.users[user]['password_hash']:
            # Password correct
            info('Successful authentication attempt by %s.' % user,
                    plugin='authdefault')
            self.users[user]['authenticated_at'] = datetime.datetime.now()
            return '%s: You are now authenticated.' % user
        else:
            # Password incorrect
            warning('Failed authentication attempt by %s.' % user,
                    plugin='authdefault')
            return '%s: The provided password is incorrect.' % user

    @command
    def deauthenticate(self, server, channel, nick, params):
        """
        Clears your authentication In order to perform a privileged command, you
        will have to authenticate again.
        """
        user = nick.split('!')[0]
        if not user in self.users:
            return '%s: You are not registered yet.' % user
        if not self.users[user]['authenticated_at']:
            return '%s: You are not authenticated.' % user
        info('%s was de-authenticated manually.' % user, plugin='authdefault')
        self.users[user]['authenticated_at'] = None
        return '%s: You are no longer authenticated.' % user

    @command
    def register(self, server, channel, nick, params):
        """
        Usage: register PASSWORD - registers your nick with the supplied
        PASSWORD, so you can authenticate in the future.
        """
        if len(params) < 1:
            return clean_string(self.register.__doc__)
        user = nick.split('!')[0]
        password = ' '.join(params)
        if user in self.users:
            return '%s: You are already registered.' % user
        info('%s registered.' % user, plugin='authdefault')
        self.users[user] = User('', datetime.datetime.now(),
                datetime.datetime.now(), hash_password(user, password))
        return '%s: You are registered and authenticated now!' % user

    @command
    @require_authenticated
    def change_password(self, server, channel, nick, params):
        """
        Usage: change_password NEW_PASSWORD - allows you to change your password
        to NEW_PASSWORD.
        """
        if len(params) < 1:
            return clean_string(self.change_password.__doc__)
        # Only authenticated users may perform this command, no additional check
        # necessary.
        user = nick.split('!')[0]
        password = ' '.join(params)
        info('%s changed their password.', plugin='authdefault')
        self.users[user]['password_hash'] = hash_password(user, password)
        # If this was the master changing their password for the first time,
        # clear the master first time flag.
        if ':new_master' in self.users and self.users[':master'] == user:
            del self.users[':new_master']
        return '%s: Your password was changed successfully!' % user

    @command
    @require_master
    def reset_password(self, server, channel, nick, params):
        """
        Usage: reset_password NICK - Upon calling this command, the password of
        NICK is set to a random string. The new password is delivered to NICK
        via query, so use this command only if the user in question is online!
        """
        if len(params) < 1:
            return clean_string(self.reset_password.__doc__)
        user = params[0]
        if not user in self.users:
            return '%s is no registered yet.' % user
        new_password = generate_password()
        self.users[user]['password_hash'] = hash_password(user, new_password)
        self.bot.client.send('PRIVMSG', 'user', ':Your password has been reset \
to: %s' % new_password)
        return 'The password of %s was reset successfully.' % user


    #############################
    # Automatically de-authenticate users on various occasions.
    # Also notify the new master to change their password, if necessary
    #############################

    def _request_pwd_change(self, nick):
        """
        If a new master is in the house, and they haven't changed their password
        yet, remind them on join, rename, and when they are talking.
        Also, authenticate the user so they can change their password.
        """
        user = nick.split('!')[0]
        if ':new_master' in self.users and user == self.users[':master']:
            self.users[user]['authenticated_at'] = datetime.datetime.now()
            self.bot.client.send('PRIVMSG', user, ':Please change your \
password as soon as possible using the change_password command!')

    def on_userjoin(self, server, channel, nick):
        """Check for new master, and request password change if applicable."""
        self._request_pwd_change(nick)

    def _try_deauthenticate(self, nick):
        """De-authenticates a user, if they exist."""
        user = nick.split('!')[0]
        if user in self.users:
            self.users[user]['authenticated_at'] = None

    def on_userpart(self, server, channel, nick, message):
        """De-authenticate user."""
        self._try_deauthenticate(nick)

    def on_userrenamed(self, server, oldnick, newnick):
        """De-authenticate user."""
        self._request_pwd_change(newnick)
        self._try_deauthenticate(oldnick)

    def on_userkicked(self, server, channel, nick, reason):
        """De-authenticate user."""
        self._try_deauthenticate(nick)

    def on_privmsg(self, server, channel, nick, message):
        """Check for new master, and request password change if applicable."""
        self._request_pwd_change(nick)


    #############################
    # Authorizer methods:
    #############################

    def _has_rank(self, nick, rank):
        """
        Determines if nick has a given rank. Defaults to false if nick is not
        registered.
        """
        user = nick.split('!')[0]
        if user in self.users and self.users[user]['authenticated_at']:
            actual_rank = self.users[user]['rank']
            if rank == 'none':
                return True
            if rank == 'voice' and actual_rank in ('voice', 'half-op', 'op',
                    'owner', 'master'):
                return True
            if rank == 'half-op' and actual_rank in ('half-op', 'op', 'owner',
                    'master'):
                return True
            if rank == 'op' and actual_rank in ('op', 'owner', 'master'):
                return True
            if rank == 'owner' and actual_rank in ('owner', 'master'):
                return True
            if rank == 'master' and actual_rank == 'master':
                return True
            return False
        return False

    def _return_failure(self, nick, channel):
        """Sends nick a message indicating that they are not authorized."""
        self.bot.client.send('PRIVMSG', channel,
                ':%s: You are not authorized to to that.' % nick.split('!')[0])

    def authorize_master(self, server, channel, nick, message, plugin, cmd):
        if self._has_rank(nick, 'master'):
            self.execute(server, channel, nick, message, plugin, cmd)
        else:
            self._return_failure(nick, channel)

    def authorize_owner(self, server, channel, nick, message, plugin, cmd):
        if self._has_rank(nick, 'owner'):
            self.execute(server, channel, nick, message, plugin, cmd)
        else:
            self._return_failure(nick, channel)

    def authorize_op(self, server, channel, nick, message, plugin, cmd):
        if self._has_rank(nick, 'op'):
            self.execute(server, channel, nick, message, plugin, cmd)
        else:
            self._return_failure(nick, channel)

    def authorize_hop(self, server, channel, nick, message, plugin, cmd):
        if self._has_rank(nick, 'hop'):
            self.execute(server, channel, nick, message, plugin, cmd)
        else:
            self._return_failure(nick, channel)

    def authorize_voice(self, server, channel, nick, message, plugin, cmd):
        if self._has_rank(nick, 'voice'):
            self.execute(server, channel, nick, message, plugin, cmd)
        else:
            self._return_failure(nick, channel)

    def authorize_authenticated(self, server, channel, nick, message, plugin,
            cmd):
        if self._has_rank(nick, 'none'):
            self.execute(server, channel, nick, message, plugin, cmd)
        else:
            self._return_failure(nick, channel)
