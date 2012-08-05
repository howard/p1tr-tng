"""
Provides convenience functions for logging. Wraps around Python's logging
module.

A word about the logging functions (debug, info, warning, error, critical):
The first parameter is the message to be logged. Additional to that, a number
of keyword arguments is supported:
* server - If only this is set, the message goes to the sever log.
* channel - Requires server to be set; the message goes to the channel's log.
* plugin - If set, server and channel are ignored. The message is written to
    the specified plugin's log.
By default, if no keyword arguments are specified, the message goes to the
global bot logfile.

Keep in mind that when logging to a channel, the severity is not displayed.
"""

import logging
import os.path

# Constants
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

_logdir = 'log'
_loglevel = logging.ERROR
_to_stderr = True
_loggers = dict()

_default_format = logging.Formatter('%(asctime)s %(levelname)s\t%(message)s')
_channel_format = logging.Formatter('%(asctime)s %(message)s')

def _clear_loggers():
    """
    Terminates the existing loggers, so they can be re-created the next time
    they are needed. This is required in order to allow changing the log
    directory and the console output option to take effect.
    """
    # Usually, shutdown should only be called on application exit, as it closes
    # all handlers. In this case, however, since all loggers are re-created, it
    # doesn't matter.
    shutdown()
    _loggers = dict()

def set_logdir(path):
    """
    All logs are written to the directory specified in the parameter. Calling
    this function will re-create all loggers as soon as they are needed the next
    time, otherwise the change would be without effect.
    """
    global _logdir
    _logdir = path
    _clear_loggers()

def set_loglevel(loglevel):
    """
    Sets the minimum required importance of a log message in order to be written
    to log. Possible values: DEBUG, INFO, WARNING, ERROR, CRITICAL. The selected
    severity and all severities to the right of it are written. You should use
    this module's constants with the appropriate names as parameters.
    """
    global _loglevel
    _loglevel = loglevel
    for logger in _loggers:
        _loggers[logger].setLevel(_loglevel)

def set_console_output(value):
    """
    Enables or disables console output of the log messages. The log level
    applies. Calling this function will re-create all loggers as soon as they
    are needed the next time, otherwise the change would be without effect.
    """
    global _to_stderr
    _to_stderr = value
    _clear_loggers()

def get_logger(name):
    """Fetches an existing logger or creates a new one, if it doesn't exist."""
    global _loglevel, _logdir, _to_stderr, _default_format, _channel_format
    if name in _loggers:
        return _loggers[name]
    # Doesn't exist. Create new one and configure it.
    logger = logging.getLogger(name)
    logger.setLevel(_loglevel)
    if name == '__global__':
        path = os.path.join(_logdir, 'global.log')
    else:
        path = os.path.join(_logdir, name + '.log')
    fmt = _channel_format if '#' in name else _default_format
    file_handler = logging.FileHandler(path)
    file_handler.setLevel(DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    if _to_stderr and not '#' in name: # Don't show console logs for channels
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(DEBUG)
        stream_handler.setFormatter(fmt)
        logger.addHandler(stream_handler)
    _loggers[name] = logger
    return _loggers[name]

def shutdown():
    logging.shutdown()

def log(severity, message, **kwargs):
    """
    Common logic for all logging functions. The severity is a lowercase string,
    e.g. debug, info, warning, error, critical.
    """
    try:
        if 'plugin' in kwargs:
            getattr(get_logger(kwargs['plugin']), severity)(message)
            return
        if 'server' in kwargs and 'channel' in kwargs:
            getattr(get_logger(kwargs['server'].split(':')[0] +
                kwargs['channel']), severity)(message)
            return
        if 'server' in kwargs:
            getattr(get_logger(kwargs['server'].split(':')[0]),
                    severity)(message)
            return
        if 'test' in kwargs:
            getattr(get_logger('test'), severity)(message)
            return
        # All remaining messages are sent to the global log.
        getattr(get_logger('__global__'), severity)(message)
    except AttributeError:
        raise ValueError('Invalid log severity "' + severity + '"')

def debug(message, **kwargs):
    """Detailed diagnostic information for debugging and development."""
    log('debug', message, **kwargs)

def info(message, **kwargs):
    """Status information during regular operation."""
    log('info', message, **kwargs)

def warning(message, **kwargs):
    """Unexpected events occured or are expected, but can be handled."""
    log('warning', message, **kwargs)

def error(message, **kwargs):
    """Part of the software malfunctions, but rest continues to work."""
    log('error', message, **kwargs)

def critical(message, **kwargs):
    """Critical error prevents continuous operation."""
    log('critical', message, **kwargs)

def plain(message, **kwargs):
    if not 'server' in kwargs or not 'channel' in kwargs \
            or 'plugin' in kwargs:
        raise ValueError('May only be used for channel logging.')
    critical(message, **kwargs)
