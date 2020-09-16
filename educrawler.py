import argparse
import yaml

from time import sleep

from educrawler.utilities import log
from educrawler.crawler import Crawler
from educrawler.constants import (
    CONST_CONFIG_FILE,
)

def main():
    """
    The main routine.

    """
    
    # Command line arguments
    PARSER = argparse.ArgumentParser(
        description="Microsoft's EduHub portal crawler."
    )

    PARSER.add_argument(
        "--fconfig",
        default=CONST_CONFIG_FILE,
        help="YAML config file (default: %s)." % (CONST_CONFIG_FILE),
    )

    args, _ = PARSER.parse_known_args()

    log("Started", level=0)

    log("Reading config file %s" % (args.fconfig), level=1)

    with open(args.fconfig, "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    crawler = Crawler(cfg["login_email"], cfg["login_password"], hide=False)

    #courses_df = crawler.get_courses_df()
    #print(courses_df)

    handouts_df, error = crawler.get_course_details("Urban analytics")

    if error is not None:
        log(error, level=0)
    else:
        print(handouts_df)

    sleep(10)

    crawler.quit()

    log("Finished", level=0)


if __name__ == "__main__":
    main()

