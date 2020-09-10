import argparse
import yaml


from educrawler.utilities import log
from educrawler.crawler import Crawler
from educrawler.constants import (
    CONST_CONFIG_FILE,
)

def main(args):
    """
    Arguments:
        args - command line arguments
    """

    log("Reading config file %s" % (args.fconfig))

    with open(args.fconfig, "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    crawler = Crawler(cfg["login_email"], cfg["login_password"], hide=False)

    #courses_df = crawler.get_courses_df()

    crawler.get_course_details("Urban analytics")

    crawler.quit()


if __name__ == "__main__":

    # Command line arguments
    PARSER = argparse.ArgumentParser(
        description="Microsoft's EduHub portal crawler."
    )

    PARSER.add_argument(
        "--fconfig",
        default=CONST_CONFIG_FILE,
        help="YAML config file (default: %s)." % (CONST_CONFIG_FILE),
    )

    ARGS, _ = PARSER.parse_known_args()

    log("Started")

    main(ARGS)

    log("Finished")
