"""
Command line tools package for crawling the Education section of portal.azure.com.

Tomas Lazauskas
"""

import os
import argparse
import yaml
import pandas as pd

from tabulate import tabulate

from src.educrawler.modules.crawler import Crawler
from src.educrawler.modules.utilities import log
from src.educrawler.modules.constants import (
    CONST_CONFIG_FILE,
    CONST_ACTION_LIST,
    CONST_OUTPUT_TABLE,
    CONST_OUTPUT_LIST,
    CONST_OUTPUT_CSV,
    CONST_OUTPUT_JSON,
    CONST_DEFAULT_OUTPUT_FILE_NAME,
    CONST_WEBDRIVER_HEADLESS,
    CONST_VERBOSE_LEVEL,
)


def set_command_line_args(default_output):
    """
    Sets up command line arguments.

    Arguments:
        default_output: default output type (table, csv, json, ..)

    Returns:
        args: command line arguments
    """

    # Command line arguments
    parser = argparse.ArgumentParser(
        description="A command line experience for interacting with the Education section of portal.azure.com."
    )

    parser.add_argument(
        "--output",
        default=default_output,
        help="Output type (default: %s)." % (default_output),
        choices=CONST_OUTPUT_LIST,
    )

    subparser = parser.add_subparsers()

    # courses

    parser_c = subparser.add_parser("course")
    parser_c.add_argument(
        "courses_action",
        default=CONST_ACTION_LIST,
        const=CONST_ACTION_LIST,
        nargs="?",
        choices=[CONST_ACTION_LIST],
    )

    # handouts

    parser_h = subparser.add_parser("handout")
    parser_h.add_argument(
        "handout_action",
        default=CONST_ACTION_LIST,
        const=CONST_ACTION_LIST,
        nargs="?",
        choices=[CONST_ACTION_LIST],
    )

    parser_h.add_argument(
        "--course-name", help="Name of course.",
    )

    parser_h.add_argument(
        "--lab-name", help="Name of lab.",
    )

    parser_h.add_argument(
        "--handout-name", help="Name of handout.",
    )

    args, _ = parser.parse_known_args()

    return args


def read_config_file(fconfig):
    """
    Parses config yaml file

    Arguments:
        fconfig: path to the configuration file
    Returns:
        cfg: data object of the parsed config yaml file
    """

    log("Reading in config file %s" % (fconfig), level=2)

    try:
        with open(fconfig, "r") as ymlfile:
            cfg = yaml.safe_load(ymlfile)
    except:
        log("Cannot read config file (%s). Stopping." % fconfig, level=0)

        cfg = None

    return cfg


def take_action(args, crawler):
    """
    The main routine to handle all command line actions.

    Arguments:
        args: command line arguments
        crawler: eduhub crawler object

    """
    results_df = None

    if hasattr(args, "courses_action"):
        if args.courses_action == CONST_ACTION_LIST:
            results_df = crawler.get_courses_df()
        else:
            log("Unrecognised subaction. Skipping.", level=0)

    elif hasattr(args, "handout_action"):

        if hasattr(args, "course_name"):
            course_name = args.course_name
        else:
            course_name = None

        if hasattr(args, "lab_name"):
            lab_name = args.lab_name
        else:
            lab_name = None

        if hasattr(args, "handout_name"):
            handout_name = args.handout_name
        else:
            handout_name = None

        if args.handout_action == CONST_ACTION_LIST:
            # all courses
            if course_name is None:
                results_df, _ = crawler.get_eduhub_details()
            # specific course (optionally, specific lab, handout)
            else:
                results_df, _ = crawler.get_course_details_df(
                    course_name, lab_name, handout_name
                )

        else:
            log("Unrecognised subaction. Skipping.", level=0)

    else:
        log("Unrecognised/unspecified action. Skipping.", level=0)

    return results_df


def output_result(output, result):
    """
    Outputs result of the action (if any) in the chosen format.

    Argument:
        output: command line argument for output
        result: result object of the previously taken action

    """

    if not isinstance(result, pd.DataFrame):
        log("Expecting result as pandas dataframe. Got %s" % (type(result)), level=0)
        return

    if output == CONST_OUTPUT_TABLE:
        print(tabulate(result, headers="keys", tablefmt="psql", showindex=False))

    elif output == CONST_OUTPUT_CSV:

        result.to_csv("%s.csv" % CONST_DEFAULT_OUTPUT_FILE_NAME)

    elif output == CONST_OUTPUT_JSON:

        result.to_json("%s.json" % CONST_DEFAULT_OUTPUT_FILE_NAME, orient="records")

    else:
        log("Unrecognised type of output. Skipping.", level=0)


def main():
    """
    The main routine.

    """
    status = True

    log("Crawler started", level=1)

    os.environ["WDM_LOG_LEVEL"] = "%d" % CONST_VERBOSE_LEVEL

    # read in config file
    config = read_config_file(CONST_CONFIG_FILE)

    if config is None:
        status = False

    if status:
        try:
            default_output = config["default_output"]
        except:
            default_output = CONST_OUTPUT_TABLE

        # set up command line arguments
        args = set_command_line_args(default_output)

        login_email = config["login_email"]
        login_password = config["login_password"]

        if (
            login_email is None
            or login_password is None
            or len(login_email) == 0
            or len(login_password) == 0
        ):

            message = "Missing login credentials. Please check the configuration yaml file. Exiting."
            log(message, level=0)

            status = False

    if status:
        result = None

        try:
            webdriver_headless = config["webdriver_headless"]
        except:
            webdriver_headless = CONST_WEBDRIVER_HEADLESS

        # instantiate the crawler
        crawler = Crawler(login_email, login_password, hide=webdriver_headless)

        # take the specified action
        if crawler.client is not None:
            result = take_action(args, crawler)

        crawler.quit()

        if result is not None:
            output_result(args.output, result)

    log("Crawler finished", level=1)


if __name__ == "__main__":

    main()
