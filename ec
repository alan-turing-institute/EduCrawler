#!/usr/bin/env python

"""
Command line tool package for crawling the Education section of portal.azure.com.

Tomas Lazauskas
"""

import sys
import os

PDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "src")

if os.environ.get("PYTHONPATH") is None:
    os.environ["PYTHONPATH"] = PDIR
else:
    os.environ["PYTHONPATH"] = os.pathsep.join([dir, os.environ.get("PYTHONPATH"),])

os.execl(sys.executable, sys.executable, "-m", "educrawler", *sys.argv[1:])
