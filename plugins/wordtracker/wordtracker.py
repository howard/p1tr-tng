from p1tr.plugin import *
from p1tr.helpers import *

class Wordtracker(Plugin):
    """Tracks how often a certain word is mentioned, and provides stats."""

    def __init__(self):
        Plugin.__init__(self)
        # Structure: {word: {channel: {nick: count}}}
        self.tracklist = self.load_storage('tracklist')

    @command
    def track(self, server, channel, nick, params):
        """
        Usage: track WORD - From this point on, the occurences of this word are
        counted. If WORD is already tracked, this command has no effect.
        """
        if len(params) < 1: # Show usage if no word is supplied
            return clean_string(self.track.__doc__)
        if params[0] in self.tracklist: # Show error if word is already tracked
            return 'Already tracking "%s".' % params[0]
        # Add to tracklist
        self.tracklist[params[0]] = {}
        return '"%s" is now being tracked.' % params[0]

    @command
    def untrack(self, server, channel, nick, params):
        """
        Usage: untrack WORD - Removes WORD from the tracklist. It will no longer
        be tracked, and all existing tracking data will be purged. If WORD is
        not tracked, this command has no effect.
        """
        if len(params) < 1: # Show usage if no word is supplied
            return clean_string(self.untrack.__doc__)
        if not params[0] in self.tracklist: # Show error if word is not tracked
            return '"%s" is not tracked.' % params[0]
        # Remove from tracklist
        del self.tracklist[params[0]]
        return '"%s" has been untracked.' % params[0]

    @command
    def tracked_words(self, server, channel, nick, params):
        """Lists all words tracked by the bot."""
        words = self.tracklist.keys()
        if len(words) < 1:
            return 'No words are being tracked.'
        return pretty_list(words)

    @command
    def wordstats(self, server, channel, nick, params):
        """
        Usage: wordstats WORD [CHANNEL | NICK] - delivers stats for WORD.
        Optionally, one may specify a channel or a nick, to limit the scope of
        the stats. Consider using the trackstats command for global stats.
        """
        if len(params) < 1: # Show usage if no word is supplied
            return clean_string(self.wordstats.__doc__)
        word = params[0]
        if not word in self.tracklist: # Unknown word
            return '"%s" is not tracked.' % word
        # Show normal stats, or specialized stats if enough parameters supplied.
        if len(params) < 2: # Normal stats
            mention_count = 0
            for channel in self.tracklist[word]:
                for user in self.tracklist[word][channel]:
                    mention_count += self.tracklist[word][channel][user]
            return '"%s" has been mentioned %d times.' % (word, mention_count)
        # Specialized stats:
        if params[1].startswith('#'): # Show channel stats
            mention_count = 0
            for user in self.tracklist[word][params[1]]:
                mention_count += self.tracklist[word][params[1]][user]
            return '"%s" has been mentioned %d times in %s.' % (word,
                    mention_count, params[1])
        else: # Show user stats
            mention_count = 0
            for channel in self.tracklist[word]:
                mention_count += self.tracklist[word][channel][params[1]]
            return '%s has mentioned "%s" %d times.' % (params[1], word,
                    mention_count)

    @command
    def trackstats(self, server, channel, nick, params):
        """
        Provides some factoids about the tracked words on a server-wide scope.
        """
        word_mentions = {}
        # Get absolute number of mentions
        for word in self.tracklist:
            word_mentions[word] = 0
            for channel in self.tracklist[word]:
                for nick in self.tracklist[word][channel]:
                    word_mentions[word] += self.tracklist[word][channel][nick]
        words = list(self.tracklist.keys())
        # Sort by mentions in ascending order
        words = sorted(words, key=lambda item: word_mentions[item])
        words.reverse()
        print(str(words))
        top_words = words[:3]
        message = 'The most popular words are: '
        message += pretty_list(
                ['%s (%d)' % (word, word_mentions[word])
                    for word in top_words])
        message += '. The least popular word is %s (%d).' % (words[-1],
                word_mentions[words[-1]])
        return message

    def on_privmsg(self, server, channel, nick, message):
        # Increase stats whenever seeing the word:
        user = nick.split('!')[0]
        for word in message.split():
            if word in self.tracklist:
                if not channel in self.tracklist[word]:
                    self.tracklist[word][channel] = {}
                if not user in self.tracklist[word][channel]:
                    self.tracklist[word][channel][user] = 0
                self.tracklist[word][channel][user] += 1
