"""
P1tr is heavily plugin-based. Those plugins are located in a plugin directory
which is either in the current working directory, the P1tr home as defined in
the config file, or in the directory of the p1tr.py script (install directory).
The plugin directories are searched in this order.

Within the plugin directory (named "plugins"), each plugin has its own folder
with the same name as the plugin, all lowercase, no spaces, no special
characters. Withing the plugin's directory, there must be a __init__.py file in
order to mark the directory as a module. There also must be a .py file with the
same name as the plugin directory, plus the file extension. This file contains
the implementation of the plugin as a class derived from p1tr.plugin.Plugin.

You may add an arbitrary number of assistive files, dependencies and so on
within the plugin folder.
"""

