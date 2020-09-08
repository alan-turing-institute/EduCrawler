"""
Utilities module.
"""

from time import sleep
from datetime import datetime, timezone

from educrawler.constants import CONST_REFRESH_SLEEP_TIME

def log(message, indent=0):
    """
    Log function.
    Arguments:
        message: log message
        indent: indentation level
    """

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    indent_str = ""
    for _ in range(indent):
        indent_str += "  "

    print("%s | %s%s" % (utc_timestamp, indent_str, message))


def wait_to_load(client, condition, value, exists):
    """
    A function that iteratively checks whether a page has been loaded by checking if a 
        particular object exists/doesn't exist.

    Arguments:
        client: chrome driver client
        condition (string): condition by which object will be identified
        value (string): value by which object will be identified
        exists (bool): True - sleep while object exists, False - sleep until object comes to existance
    """
    
    sleep_wait = True

    while sleep_wait:

        log("Sleeping while the page is loading (%f).." % (CONST_REFRESH_SLEEP_TIME), indent=2)
        sleep(CONST_REFRESH_SLEEP_TIME)

        if condition == "xpath" and not exists:
            try:
                element = client.find_elements_by_xpath(value)
                log("Found it!", indent=2)
                sleep_wait = False
            except:
                sleep_wait = True
                
        else:
            log("Undefined sleeping condition. Stopping sleeping.", indent=2)
            sleep_wait = False
