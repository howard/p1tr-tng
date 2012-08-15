"""Classes and functions enabling automated unit testing of plugins."""

import inspect
from collections import namedtuple
import sys
import unittest
from p1tr.logwrap import info, warning
from p1tr.plugin import _add_annotation, discover_plugins, load_by_name

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

    """
    The instance of the plugin-to-test is injected after instantiation of the
    class by the test runner.
    """
    plugin = None

    def setUp(self):
        """
        Prepare the plugin to be tested:
        * Replace the load_storage method with a dummy, returning a plain
          dictionary so that test data is volatile. Do the same for related
          methods. But still track the opened storage instances to reveal
          errors in this direction.
        """
        self.plugin.test_storages = []
        def _load_storage(self, identifier):
            self.test_storages.append(identifier)
            return {}
        self.plugin.load_storage = _load_storage
        def _save_storage(self, identifier=None, storage=None):
            if identifier and not identifier in self.test_storage:
                raise ValueError('Storage with the identifier "%s" not found.' \
                        % identifier)
        self.plugin.save_storage = _save_storage
        def _close_storage(self, identifier=None, storage=None):
            _save_storage(identifier, storage)
            self.test_storages.remove(identifier)
        self.plugin.close_storage = _close_storage

    def tearDown(self):
        """"""

def test(func):
    """Denotes test method."""
    return _add_annotation(func, 'test', True)

def get_suite(plugin, config, module):
    """Creates a test suite of all test cases found in module."""
    test_classes = [member[1]
        for member in inspect.getmembers(module)
        if isinstance(member[1], type) and \
                issubclass(member[1], PluginTestCase)]
    # Discover test methods and create TestCase objects based on them
    test_cases = []
    for test_class in test_classes:
        for member in inspect.getmembers(test_class):
            if hasattr(member[1], '__annotations__'):
                if 'test' in member[1].__annotations__:
                    test_cases.append(test_class(member[0]))
                    test_cases[-1].plugin = load_by_name(plugin)
                    #TODO: Add bot instance simulation
                    test_cases[-1].plugin.load_settings(config)
    return unittest.TestSuite(test_cases)

def _reduce_test_results(results):
    """Summarizes test results to a tuple with counts."""
    total = [0, 0, 0, 0, 0, 0, 0]
    for result in results:
        total[0] += len(result.errors)
        total[1] += len(result.failures)
        total[2] += len(result.skipped)
        total[3] += len(result.expectedFailures)
        total[4] += len(result.unexpectedSuccesses)
        total[5] += result.testsRun
    total[6] = sum(total[:-2]) - total[2] - total[3]  # Total gone wrong
    return tuple(total)

def run_tests(config, silent=False):
    """
    Discovers plugins and runs their test cases. Returns success as boolean.
    Logs info to test.log with the configured loglevel.
    Requires a properly loaded ConfigParser object as parameter.
    """
    info('Looking up test modules...', test=True)
    # Get test modules
    test_modules = [] # Contains tuple (module, pluginname)
    for plugin in discover_plugins(config):
        try:
            test_modules.append((getattr(getattr(
                    __import__('plugins.%s.%s_test' %
                        (plugin, plugin)), plugin),
                    plugin + '_test'), plugin))
            info('Loaded tests of plugin "%s".' % plugin, test=True)
        except ImportError:
            warning('Failed to load tests of plugin "%s". Do they exist?' %
                    plugin, test=True)
    info('Running tests...', test=True)
    # Load suites and run tests
    test_runner = unittest.TextTestRunner()
    results = [test_runner.run(case)
            for case in [get_suite(entry[1], config, entry[0])
                for entry in test_modules]]
    # Summarize results through reduction
    total = _reduce_test_results(results)
    info('%d errors, %d failures, %d skipped, %d expected failures, %d \
unexpected successes. %d of %d tests were successful.' %
            (total[0], total[1], total[2], total[3], total[4],
                total[5] - total[6], total[5]), test=True)
    if (total[6] < 1): # All tests successful
        print('\033[92m[=====SUCCESS===========================================\
=============]\033[0m')
        sys.exit(0) # Exit with success
    else:
        print('\033[91m[=====FAILURE===========================================\
=============]\033[0m')
        sys.exit(1) # Indicate test failure in exit value
