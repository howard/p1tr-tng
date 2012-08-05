from p1tr.test import *

class HelloTest(PluginTestCase):

    @test
    def hello_test(self):
        for data in self.dummy_data:
            self.assertEqual(self.plugin.hello(data.server, data.channel,
                        data.nick, data.params),
                    'Hello, %s!' % data.nick.split('!')[0])
