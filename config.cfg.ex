[General]
# Specifies the bot's base location. The contents of $home/plugins are loaded
# and treated as plugins. $home/log is the storage location for log files.
# $home/data contains the plugins' persistent storage files.
# By default, this path is empty, leading to the assumption, that the current
# working directory is the $home. 
home =
# Specifies the lowest non-ignored log severity. A log message must have this
# or a higher severity in order to be recorded.
loglevel = INFO
# If yes, the bot runs in the background, daemon-style.
background = no
# Naming a plugin in the following property will prevent it from being loaded.
# This setting overrides all server-/channel-specific settings - those may only
# extend the global blacklist.
plugin_blacklist =
# The word following the character below is interpreted as a command and passed
# on to the plugins.
signal_character = +
# P1tr processes IRC events and requests in a loop. As soon as all pending
# items are processed, the process is sent to sleep for an amount of time, which
# can be specified here. This is a polling strategy that conserves CPU time.
sleeptime = 0.2

# This is a sample configuration, demonstrating the available options.
;[SampleServer]
# The bot's nick name on this server.
;nick = P1tr-test
# If the nick name specified above is registered with NickServ, you may provide
# the password below so that the bot can identify himself. If the nick name is
# not registered, or NickServ is not available at the server, the value of the
# property will have no effect.
;nick_password =
# The user with this nickname may give the bot admin commands.
;master = NickOfBotMaster
# Network connection data:
;host = irc.freenode.net
;port = 6667
# Some servers require a password in order to connect. If this is the case,
# provide it below. Don't confuse the server password with the nick password.
;server_password =
# The global plugin blacklist may be extended on a server-wide basis. Channel
# settings can only extend the combined global/server plugin blacklist.
;plugin_blacklist =
# Each channel the bot is supposed to join has its own section which is named
# according to the pattern "ServerName|channelName". In this case, ServerName
# is "SampleServer" - this part must equal the name of the section which holds
# the general server configuration. Note that the # character specifies a
# comment in this configuration file format, which is why it is substituted by
# a bar '|'. If your channel is called #channel, the section name should be
# "SampleServer-channel".
;[SampleServer|channel]
# Some channels can only be joined if a password is provided. Leave the property
# empty if the channel is public.
;password = 
# By default, all conversations are logged. You may notice that this property is
# prefixed by "logger.". This notation is used for plugin-specific settings.
;logger.log = yes
# Plugin blacklisting is possible on a channel level. Note that this blacklist
# can only extend higher blacklists (server and global).
;plugin_blacklist =
# If a channel's settings are not changed from the default, the channel's
# section may be left empty.
;[SampleServer-anotherchannel]

