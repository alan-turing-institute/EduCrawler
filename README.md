# EduHub Crawler CLI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command line experience for interacting with the Education section of portal.azure.com.

Created and designed by <a href="https://github.com/tomaslaz">Tomas Lazauskas</a>.

## Installation

```bash
pip install git+https://github.com/tomaslaz/eduhub_crawler.git
```

## Usage

```bash
$ ec [ optional arguments ] { group } { command } { parameters }
```

```bash
usage: ec [-h] [--fconfig FCONFIG] [--output {table,csv,json}]
                   {course,handout} ...

A command line experience for interacting with the Education section of
portal.azure.com.

positional arguments:
  {course,handout}

optional arguments:
  -h, --help            show this help message and exit
  --fconfig FCONFIG     YAML config file (default: config.yml).
  --output {table,csv,json}
                        Output type (default: table).
```

### Examples

- Getting a list of courses and their details (excl. Consumed)

```bash
ec course list
```

```
+----------------------------------------------+-------------------+------------+------------+------------------+
| Name                                         | Assigned credit   | Consumed   |   Students |   Project groups |
|----------------------------------------------+-------------------+------------+------------+------------------|
| Research Engineering                         | $10,000.00        | --         |         10 |                2 |
| ungrouped                                    | $20,000.00        | --         |          7 |                2 |
| TEST                                         | $10.00            | --         |          1 |                1 |
+----------------------------------------------+-------------------+------------+------------+------------------+
```

- Getting a list of all handouts and their details

```bash
ec handout list
```

- Getting details of all handouts in a particular course


```bash
ec handout list --course-name TEST
```

```
---------------+------------+-------------------+------------------+--------------------+------------------+---------------------+--------------------------------------+-----------------------+----------------------------------------------+----------------------------+
| Course name   | Lab name   | Handout name      | Handout budget   | Handout consumed   | Handout status   | Subscription name   | Subscription id                      | Subscription status  | Subscription users                           | Crawl time utc             |
|---------------+------------+-------------------+------------------+--------------------+------------------+---------------------+--------------------------------------+-----------------------+----------------------------------------------+---------------------------|
| TEST          | project    | test_subscription | $2.00            | $0.00              | done             | test_subscription   | ***                                  | Canceled              | ['***']                                     | 2020-09-23 13:20:47.655825 |
+---------------+------------+-------------------+------------------+--------------------+------------------+---------------------+--------------------------------------+---------------------+------------------------------------------_----+----------------------------+
```

- Getting details of all handouts in a particular course from a particular lab

```bash
ec handout list --course-name TEST --lab-name project
```

- Getting details of a particular handout in a particular course from a particular lab

```bash
ec handout list --course-name "Research Engineering" --lab-name "project" --handout-name "Tomas Lazauskas"
```

```
+----------------------+------------+-----------------+------------------+--------------------+------------------+---------------------+--------------------------------------+-----------------------+----------------------------------------------+----------------------------+
| Course name          | Lab name   | Handout name    | Handout budget   | Handout consumed   | Handout status   | Subscription name   | Subscription id                      | Subscription status   | Subscription users                           | Crawl time utc             |
|----------------------+------------+-----------------+------------------+--------------------+------------------+---------------------+--------------------------------------+-----------------------+----------------------------------------------+----------------------------|
| Research Engineering | project    | Tomas Lazauskas | $300.00          | $165.95            | done             | Tomas Lazauskas     | ***                                  | Active                | ['***']                                      | 2020-09-23 13:47:07.161545 |
+----------------------+------------+-----------------+------------------+--------------------+------------------+---------------------+--------------------------------------+-----------------------+----------------------------------------------+----------------------------+
```
