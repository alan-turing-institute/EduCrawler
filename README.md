# EduHub Crawler CLI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command line experience for interacting with the Education section of portal.azure.com.

Created and designed by <a href="https://github.com/tomaslaz">Tomas Lazauskas</a>.

## Installation

```bash
pip install git+https://github.com/alan-turing-institute/EduCrawler.git
```

## Setup

Set the required and optional environmental parameters (recommended by modifying the `~/.bash_profile` file).

```bash
# EduCrawler
export EC_EMAIL="example@mail.com" # required
export EC_PASSWORD="password" # required
export EC_VERBOSE_LEVEL=2 # optional (choices: 0-4, 0 - min, 4 - max, default: 2)
export EC_DEFAULT_OUTPUT="table" # optional (choices: json, csv, table)
export EC_HIDE=true # optional (default: true) # hide browser
export EC_MFA=true # optional (default: true) # authetication uses mfa
```

Do not forget either restart the terminal or use the `source` command to effect the changes.

## Usage

```bash
$ ec [ optional arguments ] { group } { command } { parameters }
```

```bash
usage: ec [-h] [--output {table,csv,json}] {course,handout} ...

A command line experience for interacting with the Education section of
portal.azure.com.

positional arguments:
  {course,handout}

optional arguments:
  -h, --help            show this help message and exit
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
+---------------+------------+-------------------+------------------+--------------------+------------------+---------------------+--------------------------------------+-----------------------+----------------------------+----------------------------------------------+----------------------------+
| Course name   | Lab name   | Handout name      | Handout budget   | Handout consumed   | Handout status   | Subscription name   | Subscription id                      | Subscription status   | Subscription expiry date   | Subscription users                           | Crawl time utc             |
|---------------+------------+-------------------+------------------+--------------------+------------------+---------------------+--------------------------------------+-----------------------+----------------------------+----------------------------------------------+----------------------------|
| TEST          | project    | test_subscription | $2.00            | $0.00              | done             | test_subscription   | ***                                  | Canceled              | 2020-09-30                 | ['***']                                      | 2020-09-30 10:22:13.065071 |
+---------------+------------+-------------------+------------------+--------------------+------------------+---------------------+--------------------------------------+-----------------------+----------------------------+----------------------------------------------+----------------------------+
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
+----------------------+------------+-----------------+------------------+--------------------+------------------+---------------------+--------------------------------------+-----------------------+----------------------------+----------------------------------------------+----------------------------+
| Course name          | Lab name   | Handout name    | Handout budget   | Handout consumed   | Handout status   | Subscription name   | Subscription id                      | Subscription status   | Subscription expiry date   | Subscription users                           | Crawl time utc             |
|----------------------+------------+-----------------+------------------+--------------------+------------------+---------------------+--------------------------------------+-----------------------+----------------------------+----------------------------------------------+----------------------------|
| Research Engineering | project    | Tomas Lazauskas | $300.00          | $166.90            | done             | Tomas Lazauskas     | ***                                  | Active                | 2020-09-30                 | ['***']                                      | 2020-09-30 10:25:27.822008 |
+----------------------+------------+-----------------+------------------+--------------------+------------------+---------------------+--------------------------------------+-----------------------+----------------------------+----------------------------------------------+----------------------------+
```

## Getting help
If you found a bug or need support, please submit an issue [here](https://github.com/alan-turing-institute/EduCrawler/issues/new).

## How to contribute
We welcome contributions! If you are willing to propose new features or have bug fixes to contribute, please submit a pull request [here](https://github.com/alan-turing-institute/EduCrawler/pulls).