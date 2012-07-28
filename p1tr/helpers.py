"""Generally useful helper functions, possibly for use in plugins."""

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
    
    return ('%s %s %s %s' % (add_unit(days, 'day', 'days'),
            add_unit(hours, 'hour', 'hours'),
            add_unit(minutes, 'minute', 'minutes'),
            add_unit(seconds, 'second', 'seconds'))).strip()
