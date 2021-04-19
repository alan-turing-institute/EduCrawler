"""
Constants module.
"""

import os

CONST_PORTAL_ADDRESS = "https://portal.azure.com/"
CONST_PORTAL_OVERVIEW_ADDRESS = "https://portal.azure.com" + \
    "/#blade/Microsoft_Azure_Education/EducationMenuBlade/overview"
CONST_PORTAL_COURSES_ADDRESS = "https://portal.azure.com" + \
    "/#blade/Microsoft_Azure_Education/EducationMenuBlade/classrooms"

CONST_WEBDRIVER_HEADLESS = True

try:
    CONST_VERBOSE_LEVEL = int(os.environ["EC_VERBOSE_LEVEL"])
except KeyError:
    CONST_VERBOSE_LEVEL = 2

CONST_REFRESH_SLEEP_TIME = 0.05
CONST_MAX_REFRESH_COUNT = 200
CONST_SLEEP_TIME = 1.5
CONST_TIMEOUT = 30

CONST_USAGE_ACTION = "usage_action"

CONST_ACTION_LIST = "list"

CONST_OUTPUT_TABLE = "table"
CONST_OUTPUT_CSV = "csv"
CONST_OUTPUT_JSON = "json"
CONST_OUTPUT_DF = "df"
CONST_OUTPUT_LIST = [CONST_OUTPUT_TABLE, CONST_OUTPUT_CSV, CONST_OUTPUT_JSON]

CONST_DEFAULT_OUTPUT_FILE_NAME = "ec_output"

CONST_USAGE_PATH = "/tmp/"
CONST_USAGE_CSV_FILE_NAME = "azure-usage.csv"