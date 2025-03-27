# Redfish Use Case Checkers

Copyright 2017-2025 DMTF. All rights reserved.

## About

The Redfish Use Case Checkers performs common management use cases to ensure a Redfish service meets functional expectations.

## Installation

From PyPI:

    pip install redfish_use_case_checkers

From GitHub:

    git clone https://github.com/DMTF/Redfish-Use-Case-Checkers.git
    cd Redfish-Use-Case-Checkers
    python setup.py sdist
    pip install dist/redfish_use_case_checkers-x.x.x.tar.gz

## Requirements

The Redfish Use Case Checkers requires Python3.

Required external packages:

```
colorama
redfish
redfish_utilities
```

If installing from GitHub, you may install the external packages by running:

    pip install -r requirements.txt

## Usage

```
usage: rf_use_case_checkers.py [-h] --user USER --password PASSWORD --rhost
                               RHOST [--report-dir REPORT_DIR] [--relaxed]
                               [--test-list [{AccountManagement,PowerControl,BootOverride,ManagerEthernetInterfaces} ...]]
                               [--debugging]

Validate Redfish services against use cases

options:
  -h, --help            show this help message and exit
  --user USER, -u USER  The username for authentication
  --password PASSWORD, -p PASSWORD
                        The password for authentication
  --rhost RHOST, -r RHOST
                        The address of the Redfish service (with scheme)
  --report-dir REPORT_DIR
                        The directory for generated report files (default:
                        'reports')
  --relaxed             Allows for some failures to be logged as warnings;
                        useful if the criteria is to meet the literal 'shall'
                        statements in the specification.
  --test-list [{AccountManagement,PowerControl,BootOverride,ManagerEthernetInterfaces} ...]
                        Selects specific tests to perform instead of running
                        the entire test suite.
  --debugging           Controls the verbosity of the debugging output; if not
                        specified only INFO and higher are logged.
```

Example:

    rf_use_case_checkers -r https://192.168.1.100 -u USERNAME -p PASSWORD

## Release Process

1. Go to the "Actions" page
2. Select the "Release and Publish" workflow
3. Click "Run workflow"
4. Fill out the form
5. Click "Run workflow"
