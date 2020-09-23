# EduHub Crawler CLI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command line experience for managing the Education section of portal.azure.com.

Created and designed by <a href="https://github.com/tomaslaz">Tomas Lazauskas</a>.

## Installation

## Usage

```bash
$ ec [ group ] [ command ] {parameters}
```

```bash
usage: ec [-h] [--fconfig FCONFIG] [--output {table,csv,json}]
                   {course,handout} ...

Command line tools package for crawling the Education section of
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
./ec course list
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
./ec handout list
```

- Getting a list of all handouts in a particular course


```bash
./ec handout list --course-name TEST
```


<!-- ./ec --fconfig test_config.yml handout list --course-name TEST --lab-name project --handout-name test_subscription -->