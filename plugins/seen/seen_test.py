from p1tr.test import *
from p1tr.helpers import *

class SeenTest(PluginTestCase):

    def hello_test(self):
        for data in self.dummy_data:
            self.assertEqual(self.plugin.hello(data.server, data.channel,
                        data.nick, data.params),
                    'Hello, %s!' % data.nick.split('!')[0])

    @test
    def seen_invalid_test(self):
        """Test wrong use of the command."""
        for data in self.dummy_data:
            self.assertEqual(self.plugin.seen(data.server, data.channel,
                        data.nick, []),
                    clean_string(self.plugin.seen.__doc__))

    def _was_seen_just_now(self, data, target_nick):
        self.assertEqual(self.plugin.seen(data.server, data.channel,
                target_nick, data.nick.split('!')[0]),
            '%s was last seen 0 seconds ago in %s, saying "%s".' % (
                data.nick.split('!')[0], data.channel,
                ' '.join(data.params)))

    @test
    def seen_privmsg_test(self):
        """Tests for a target that has been seen in a privmsg."""
        data = self.dummy_data[0]
        # Simulate seeing the target
        self.plugin.on_privmsg(data.server, data.channel, data.nick,
                ' '.join(data.params))
        # Check if seeing the target was registered
        self._was_seen_just_now(data, self.dummy_data[1].nick)

    @test
    @unittest.expectedFailure
    def seen_unknown_test(self):
        """Tests result when queried for unknown target."""
        self._was_seen_just_now(self.dummy_data[-1],
                self.dummy_data[-2].nick.split('!')[0])

    @test
    def seen_join_test(self):
        """Test for a target that has been seen on join."""
        data = self.dummy_data[0]
        self.plugin.on_userjoin(data.server, data.channel, data.nick)
        self.assertEqual(self.plugin.seen(data.server, data.channel,
                    self.dummy_data[1].nick, data.nick.split('!')[0]),
                '%s was last seen 0 seconds ago in %s, joining the channel.' % (
                    data.nick.split('!')[0], data.channel))

    @test
    def seen_part_test(self):
        """Test for a target that has been seen on part."""
        self.assertTrue(False)
