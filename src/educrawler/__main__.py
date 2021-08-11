"""
Command line tools package for crawling the Education section of
    portal.azure.com.

Tomas Lazauskas
"""

import os
import argparse

from educrawler.crawler import crawl

from educrawler.constants import (
    CONST_OUTPUT_LIST,
    CONST_ACTION_LIST,
    CONST_USAGE_ACTION,
    CONST_OUTPUT_TABLE,
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
        description="A command line experience for interacting with "
        + "the Education section of portal.azure.com."
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
        "--course-name",
        help="Name of course.",
    )

    parser_h.add_argument(
        "--lab-name",
        help="Name of lab.",
    )

    parser_h.add_argument(
        "--handout-name",
        help="Name of handout.",
    )

    # usage
    parser_u = subparser.add_parser("usage")
    parser_u.add_argument(
        CONST_USAGE_ACTION,
        default=CONST_USAGE_ACTION,
        const=CONST_USAGE_ACTION,
        nargs="?",
        choices=[CONST_USAGE_ACTION],
    )

    args, _ = parser.parse_known_args()

    return args


def main():
    """
    The main routine.

    """

    try:
        default_output = os.environ["EC_DEFAULT_OUTPUT"]
    except KeyError:
        default_output = CONST_OUTPUT_TABLE

    # set up command line arguments
    args = set_command_line_args(default_output)

    # run the crawl
    _, _, _ = crawl(args)


if __name__ == "__main__":

    main()
