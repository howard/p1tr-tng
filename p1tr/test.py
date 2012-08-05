"""Classes and functions enabling automated unit testing of plugins."""

from collections import namedtuple
import unittest

"""Container for dummy test data sets."""
DummyData = namedtuple('DummyData',
        ['server', 'channel', 'nick', 'params', 'message'])

class PluginTestCase(unittest.TestCase):
    """
    Specialized test case class for testing P1tr plugins.
    The main difference between this test case class and unittest.TestCase is
    that most of the test fixture is set up behind the scenes, either by this
    class, or the test runner implemented in the p1tr.test module.
    """
    #TODO: finish documentation

    """
    Dummy data, covering important extreme cases. The number of available
    entries is synchronized intentionally to enable looping over the test data
    for easily testing various scenarios.
    """
    dummy_data = [
            DummyData(
                server='irc.example.org', channel='#p1tr',
                nick='7', params=['text', ''],
                message='text'),
            DummyData(
                server='example.customtld', channel='##p1tr',
                nick='RegularNick', params=[],
                message=''),
            DummyData(
                server='example.customtld', channel='##p1tr',
                nick='regularnick', params=[],
                message=''),
            DummyData(
                server='localnetserver', channel='&p1tr',
                nick='longnickn', params=['äöü', '@&%$§'],
                message='äöü     @&%$§'),
            DummyData(
                server='123example.org', channel='#MaximumChannelNameLengthIs20\
0Characters.TheProtocolPermitsPrettyMuchAnythingApartFromCommasSpacesAndThe^GCo\
trolCharacter__________________________________________________________________\
____', nick='longnickn', params=['text'], message="  \ttext ")
            ]


    def __init__(self, plugin_instance):
        """Injects a plugin instance to be used in test methods."""
        unittest.TestCase.__init__(self)
        self.plugin = plugin_instance

    def setUp(self):
        """"""
    def tearDown(self):
        """"""


def get_testcases(module):
    """
    Finds all test cases in the supplied module and returns instances of those
    as a list. Note that only test cases derived from PluginTestCase will be
    used.
    """
    #TODO

def run_tests(config):
    """
    Discovers plugins and runs their test cases. Returns success as boolean.
    Logs info to test.log with the configured loglevel.
    Requires a properly loaded ConfigParser object as parameter.
    """
