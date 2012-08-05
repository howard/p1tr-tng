import datetime
from p1tr.helpers import clean_string, humanize_time
from p1tr.plugin import *

@meta_plugin
class Memo(Plugin):
    """
    Delivers messages to absent users as soon as they return or become active
    again.
    """

    def __init__(self):
        Plugin.__init__(self)
        # Structure of mailbag:
        # {'recipient': [(sender, time, message, confidential_flag)]}
        self._mailbag = self.load_storage('mailbag')

    def _try_deliver(self, nick, channel):
        """
        Sends waiting memos to the specified user. Respects the confidentiality
        flag.
        """
        user = nick.split('!')[0]
        if user in self._mailbag:
            for memo in self._mailbag[user]:
                message = '%s: %s left a memo for you %s ago: %s' % \
                    (user, memo[0],
                            humanize_time(datetime.datetime.now() - memo[1]),
                            memo[2])
                if memo[3]: # Is confidential
                    self.bot.client.send('PRIVMSG', user, ':' + message)
                else:
                    self.bot.client.send('PRIVMSG', channel, ':' + message)
                self._mailbag[user].remove(memo)

    def _add_message(self, recipient, sender, message, is_confidential):
        """Adds a memo for recipient to the mailbag."""
        if not recipient in self._mailbag:
            self._mailbag[recipient] = []
        self._mailbag[recipient].append(
                (sender, datetime.datetime.now(), message, is_confidential))

    @command
    def memo(self, server, channel, nick, params):
        """
        Usage: memo RECIPIENT MESSAGE - delivers MESSAGE to RECIPIENT as soon as
        they join a channel where I am present, or they show any other activity.
        For confidential delivery, use the classified_memo command.
        """
        if len(params) < 2:
            return clean_string(self.memo.__doc__)
        self._add_message(params[0], nick.split('!')[0], ' '.join(params[1:]),
                False)
        return 'Your memo will be delivered ASAP.'

    @command
    def classified_memo(self, server, channel, nick, params):
        """
        Usage: classified_memo RECIPIENT MESSAGE - delivers MESSAGE to RECIPIENT
        as soon as they join a channel where I am present, or show any other
        activity. The message is delivered via query.
        """
        if len(params) < 2:
            return clean_string(self.classified_memo.__doc__)
        self._add_message(params[0], nick.split('!')[0], ' '.join(params[1:]),
                True)
        return 'Your classified memo will be delifered ASAP.'

    @command
    def pending_memos(self, server, channel, nick, params):
        """Returns number of not yet delivered memos."""
        memo_count = 0
        for user in self._mailbag:
            for memo in self._mailbag[user]:
                memo_count += 1
        return '%d memos are waiting for delivery.' % memo_count

    # Listeners to detect user activity:
    def on_privmsg(self, server, channel, nick, message):
        self._try_deliver(nick, channel)

    def on_userjoin(self, server, channel, nick):
        self._try_deliver(nick, channel)

    def on_useraction(self, server, channel, nick, message):
        self._try_deliver(nick, channel)
