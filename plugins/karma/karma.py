from random import choice
import datetime
from p1tr.plugin import *
from p1tr.helpers import *


"""Possible comments about certain karma levels."""
karma_comments = {
        'very low': [
            '%s has become evil itself',
            'we will suffer under the reign of evil genius %s',
            '%s seems to be quite an asshole',
            '%s will probably be reincarnated as a rock'
            ],
        'low': [
            '%s is a tad on the bad side',
            'watch out, %s is a mean bastard',
            "%s has a master's degree in wickedness",
            '%s is a bad person'
            ],
        'negative': [
            "%s's karma is out of ballance",
            '%s is tempted by the dark side',
            '%s is like a gang of nerds listening to gangster rap',
            'fix your karma, %s!'
            ],
        'neutral': [
            '%s is totally zen',
            '%s is on a highway to he--, er, Nirvana',
            '%s has no strong feelings, one way or another',
            "%s is this channel's switzerland"
            ],
        'positive': [
            '%s manages to be just well-behaved enough',
            '%s is alright',
            '%s just started his career at doing good',
            '%s fails at being bad'
            ],
        'high': [
            '%s is a very kind person',
            'apparently, %s helps out quite a lot',
            "it's good to have %s around",
            "%s is this channel's really nice guy"
            ],
        'very high': [
            '%s is made of cupcakes',
            '%s shits rainbows and farts unicorns',
            "%s is Gandhi's role model",
            '%s came from the future to save the world'
            ]
        }

def get_comment(karma_level):
    """
    Picks a random comment from the appropriate category in karma_comments,
    so that the content of the message correlates with the user's karma level.
    """
    if karma_level < -31:
        return choice(karma_comments['very low'])
    if karma_level < -11:
        return choice(karma_comments['low'])
    if karma_level < 0:
        return choice(karma_comments['negative'])
    if karma_level < 1:
        return choice(karma_comments['neutral'])
    if karma_level < 11:
        return choice(karma_comments['positive'])
    if karma_level < 31:
        return choice(karma_comments['high'])
    return choice(karma_comments['very high'])


class Karma(Plugin):
    """
    Modify people's karma by writing their nick, postfixed with ++ or --.
    Example: sebner++, P1tr--. You can access statistics using the karma
    command. Some words may not be tracked - see the karma_exceptions command.
    The nick whose karma should be changed must always be at the beginning of a
    message.
    """

    def __init__(self):
        Plugin.__init__(self)
        # Structure: {nick: [positive, negative, last_change_time]}
        # Using a list instead of a tuple because tuple's immutability hinders
        # in-place changes. Creating a new tuple for every single karma change
        # is a waste.
        self.karma = self.load_storage('karma')

    def load_settings(self, config):
        """Loads words whose karma should not be tracked from config."""
        self.exceptions = read_or_default(config, 'General', 'karma.exceptions',
                [], lambda val: val.split())

    @command
    def karmastats(self, server, channel, nick, params):
        """
        Usage: karma [NICK] - delivers statistics about karma. If NICK is
        supplied, the specified NICK's statistics will be displayed instead,
        if available.
        """
        if len(params) < 1: # General stats
            if len(self.karma.keys()) < 1:
                return "I don't have any karma data yet."
            total = [0, 0] # Absolute count of used karma points
            extremes = [None, None] # Highes and lowest values
            most_nice = 'unknown' # Corresponds to extremes[0]
            most_evil = 'unknown' # Corresponds to extremes[1]
            for nick in self.karma:
                ballance = self.karma[nick][0] - self.karma[nick][1]
                total[0] += self.karma[nick][0]
                total[1] += self.karma[nick][1]
                if not extremes[0] or ballance > extremes[0]: # New most nice
                    most_nice = nick
                    extremes[0] = ballance
                if not extremes[1] or ballance < extremes[1]: # New most evil
                    most_evil = nick
                    extremes[1] = ballance
            return clean_string('Overall, %d positive and %d negative karma \
                    commands were issued, resulting in a global karma balance \
                    of %d. %s is the nicest user with %d karma. %s is the most \
                    evil user with %d karma.' % (total[0], total[1],
                        total[0] - total[1], most_nice, extremes[0], most_evil,
                        extremes[1]))
        # Nick-specific stats
        if not params[0] in self.karma:
            return 'I have no karma information about %s.' % params[0]
        positive = self.karma[params[0]][0]
        negative = self.karma[params[0]][1]
        ballance = positive - negative
        return 'Karma ballance of %s: +%d -%d = %d - %s' % (params[0],
                positive, negative, ballance, get_comment(ballance) % params[0])

    @command
    @require_op
    def nirvana(self, server, channel, nick, params):
        """
        Usage: nirvana NICK - sets the supplied NICK's karma to 0, so the user
        can finally enter long-awaited Nirvana.
        """
        if len(params) < 1:
            return clean_string(self.nirvana.__doc__)
        target = params[0]
        if not target in self.karma:
            return '%s already has a clean slate.' % target
        del self.karma[target]
        return "%s's karma has been neutralized." % target

    @command
    def karma_exceptions(self, server, channel, nick, params):
        """Prints all words whose karma can not be tracked."""
        return pretty_list(self.exceptions)

    def _change_karma(self, nick, target, mode):
        """
        Changes target's karma. If mode is True, karma is increased by 1.
        Otherwise, it's decreased by 1. If nick equals target, an error message
        is returned.
        """
        if nick == target:
            return "You can't modify your own karma."
        if target in self.karma and (datetime.datetime.now() -
                self.karma[target][2]).seconds < 5:
            return 'Karma spamming is prohibited.'
        if not target in self.karma:
            self.karma[target] = [0, 0, datetime.datetime.now()]
        if mode: # Increase
            self.karma[target][0] += 1
        else: # Decrease
            self.karma[target][1] += 1
        self.karma[target][2] = datetime.datetime.now()

    def on_privmsg(self, server, channel, nick, message):
        """Listens for nick++ and nick--."""
        user = nick.split('!')[0]
        words = message.split()
        if len(words) < 1:
            return
        word = words[0]
        if not word[:-2] in self.exceptions:
            if word.endswith('++'):
                return self._change_karma(user, word[:-2], True)
            elif word.endswith('--'):
                return self._change_karma(user, word[:-2], False)
