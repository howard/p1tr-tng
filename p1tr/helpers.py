"""Generally useful helper functions, possibly for use in plugins."""

"""Values causing True to be returned when calling boolify."""
BOOLIFY_TRUE = ('true', 'yes', 'y', '1', 'on')

def boolify(string):
    """
    Returns true or false, depending on the content of the supplied string.
    Case doesn't matter.
    (TRUE, True, true, YES, yes, Yes, y, Y, 1, ON, On, on) -> True
    Everything else -> False
    """
    return string.lower() in BOOLIFY_TRUE


class BotError(Exception):
    """Raised on configuration- and non-plugin errors."""

def clean_string(string):
    """
    Converts whitespace (includes newlines etc.) to single spaces. Useful to
    avoid problems with the IRC protocol, which treats newlines, for example,
    as message terminator.
    """
    if isinstance(string, bytes):
        string = string.decode('utf-8')
    return ' '.join(string.split())

def humanize_time(delta):
    """
    Converts a timespan provided as a datetime object into a human-readable
    format.
    "Inspired" by the time_ago_in_words function in P1tr Legacy.
    """
    days = delta.days
    minutes = delta.seconds // 60
    seconds = delta.seconds - minutes * 60
    hours = minutes // 60
    minutes = minutes - hours * 60

    def add_unit(value, singular_unit, plural_unit):
        if value:
            unit = singular_unit if value == 1 else plural_unit
            return '%s %s' % (value, unit)
        else:
            return ''

    # Exception for zero-duration: return 0 seconds
    if days < 1 and hours < 1 and minutes < 1 and seconds < 1:
        return '0 seconds'

    return ('%s %s %s %s' % (add_unit(days, 'day', 'days'),
            add_unit(hours, 'hour', 'hours'),
            add_unit(minutes, 'minute', 'minutes'),
            add_unit(seconds, 'second', 'seconds'))).strip()

def pretty_list(lst, joiner=', ', stringifier=str):
    """
    Turns a list into a string with all elements joined together. By default,
    the elements are joined with ', ' - this can be changed optionally.
    The list can contain any type of object, since str() is called. For some
    types, you may want to consider implementing the __str__() method.
    Alternatively, you can provide the optional stringifier parameter, which
    requires a function with one parameter, returning a string as value.
    A nice alternative use for the stringifier is a function that modifies a
    list value (for example converts the case).
    """
    return joiner.join([stringifier(elem) for elem in lst])
