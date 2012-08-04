#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Usage: $0 PLUGIN_NAME [BOT_HOME]"
    exit 1
fi

if [ $# -lt 2 ]; then
    BOT_HOME=$2
else
    BOT_HOME=.
fi

PLUGIN_NAME=$1
PLUGIN_DIR=$BOT_HOME/plugins/$PLUGIN_NAME
# Abort if there already is a plugin with this name.
if [ -e $PLUGIN_DIR ]; then
    echo "Error: A plugin with this name exists already."
    exit 2
fi

mkdir $PLUGIN_DIR
touch $PLUGIN_DIR/__init__.py

PLUGIN_FILE=$PLUGIN_DIR/$PLUGIN_NAME.py
CLASS_NAME="${PLUGIN_NAME[@]^}"
cat << EOF | cat > $PLUGIN_FILE
from p1tr.plugin import *
from p1tr.helpers import *

class $CLASS_NAME(Plugin):
    """This text will be the plugin description in the help message."""

    @command
    def myCommand(self, server, channel, nick, params):
        """
        Command can be called via !myCommand, if ! is the signal character. This text
        will be displayed when looking for help on this command.
        """
        return "This text is sent as a response to the command."

EOF
