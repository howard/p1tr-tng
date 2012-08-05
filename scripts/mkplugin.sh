#!/bin/bash

# Check if plugin name is specified. If not, print usage and exit.
if [ $# -lt 1 ]; then
    echo "Usage: $0 PLUGIN_NAME [BOT_HOME] - creates a scaffold plugin with the specified name. If BOT_HOME is not supplied, the current working directory will be assumed. BOT_HOME must contain a plugins directory."
    exit 1
fi

# Since the bot home is optional, check if the parameter is set, and use the
# default if not.
if [ $# -lt 2 ]; then
    BOT_HOME=.
else
    BOT_HOME=$2
fi

PLUGIN_NAME=$1
PLUGIN_DIR=$BOT_HOME/plugins/$PLUGIN_NAME
# Abort if there already is a plugin with this name.
if [ -e $PLUGIN_DIR ]; then
    echo "Error: A plugin with this name exists already."
    exit 2
fi

# Create plugin module
mkdir $PLUGIN_DIR
touch $PLUGIN_DIR/__init__.py

# Create dummy implementation
CLASS_NAME="${PLUGIN_NAME[@]^}"
cat << EOF | cat > $PLUGIN_DIR/$PLUGIN_NAME.py
from p1tr.plugin import *
from p1tr.helpers import *

class $CLASS_NAME(Plugin):
    """This text will be the plugin description in the help message."""

    @command
    def myCommand(self, server, channel, nick, params):
        """
        Command can be called via !myCommand, if ! is the signal character. This
        text will be displayed when looking for help on this command.
        """
        return 'This text is sent as a response to the command.'

EOF

# Create dummy test case
CLASS_NAME="$CLASS_NAME"Test
cat << EOF | cat > "$PLUGIN_DIR/$PLUGIN_NAME"_test.py
from p1tr.plugin import *
from p1tr.test import *

class $CLASS_NAME(PluginTestCase):
    """This is a dummy test case for the generated plugin scaffold."""

    def setUp(self):
        super(PluginTestCase, self)
        # Perform any setup task, but call the parent method first.

    def tearDown(self):
        super(PluginTestCase, self)
        # Same goes for tearDown. If you don't need setUp or tearDown, you can
        # just omit them, though.
    
    def myCommand_test(self):
        """
        This test runs the command with various parameters, checking if it is
        fit for extreme cases.
        """
        expected = 'This text is sent as a response to the command.'
        # Dummy values for common parameters are included in this class. There
        # are several for each. You can check all of them using a loop.
        # Also, you already have an instance of the plugin available:
        for data in self.dummy_data:
            ret_val = self.plugin.myCommand(data.server, data.channel,
                    data.nick, data.params)
            self.assertEqual(expected, ret_val)
EOF

echo "Develop your plugin by editing the file $PLUGIN_DIR/$PLUGIN_NAME.py"
