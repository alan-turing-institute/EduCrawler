"""
Command line tool package for crawling the Education section of portal.azure.com.

Tomas Lazauskas
"""

from datetime import datetime
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
    CONST_TIME_FILE_FORMAT,
)


def set_command_line_args():
    """
    Sets up command line arguments.

    Returns:
        args: command line arguments
    """

    # Command line arguments
    parser = argparse.ArgumentParser(
        description="Package for crawling the Education section of portal.azure.com."
    )

    parser.add_argument(
        "--fconfig",
        default=CONST_CONFIG_FILE,
        help="YAML config file (default: %s)." % (CONST_CONFIG_FILE),
    )

    parser.add_argument(
        "--output",
        default=CONST_OUTPUT_TABLE,
        help="Output type (default: %s)." % (CONST_OUTPUT_TABLE),
        choices=CONST_OUTPUT_LIST,
    )

    subparser = parser.add_subparsers()

    parser_courses = subparser.add_parser("course")
    parser_courses.add_argument(
        "courses_action",
        default=CONST_ACTION_LIST,
        const=CONST_ACTION_LIST,
        nargs="?",
        choices=[CONST_ACTION_LIST],
    )

    # parser_handout = subparser.add_parser("handout")
    # parser_handout.add_argument(
    #     "handout_action",
    #     default=CONST_ACTION_LIST,
    #     const=CONST_ACTION_LIST,
    #     nargs="?",
    #     choices=[CONST_ACTION_LIST],
    # )

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

    with open(fconfig, "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

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

        if args.handout_action == CONST_ACTION_LIST:
            results_df = crawler.get_eduhub_details()
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
        print(tabulate(result, headers="keys", tablefmt="psql"))

    elif output == CONST_OUTPUT_CSV:
        output_file = "ec_output_%s.csv" % datetime.now().strftime(
            CONST_TIME_FILE_FORMAT
        )
        result.to_csv(output_file)

    elif output == CONST_OUTPUT_JSON:
        print(result.to_json(orient="records"))

    else:
        log("Unrecognised type of output. Skipping.", level=0)


def main():
    """
    The main routine.

    """

    log("Crawler started", level=1)

    # set up command line arguments
    args = set_command_line_args()

    # read in config file
    config = read_config_file(args.fconfig)

    login_email = config["login_email"]
    login_password = config["login_password"]

    # instantiate the crawler
    crawler = Crawler(login_email, login_password, hide=False)

    # take the specified action
    if crawler.client is not None:
        result = take_action(args, crawler)

    crawler.quit()

    if result is not None:
        output_result(args.output, result)

    log("Crawler finished", level=1)


if __name__ == "__main__":
    main()
