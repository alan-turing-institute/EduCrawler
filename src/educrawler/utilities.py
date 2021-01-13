"""
Utilities module.
"""

from datetime import datetime, timezone

from educrawler.constants import CONST_VERBOSE_LEVEL


def log(message, level=3, indent=0):
    """
    Log output to screen.

    Arguments:
        message: log message
        level:
            0 - warning, error messages (minimal)
            1 - warning, error, info messages (normal)
            2 - warning, error, info, debug messages (debug)
            3 - all messages (all)
        indent: indentation level
    """

    if level <= CONST_VERBOSE_LEVEL:
        utc_timestamp = datetime.utcnow() \
            .replace(tzinfo=timezone.utc).isoformat()

        indent_str = ""
        for _ in range(indent):
            indent_str += "  "

        print("%s | %s%s" % (utc_timestamp, indent_str, message))
