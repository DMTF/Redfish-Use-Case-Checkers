# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

"""
Redfish Use Case Checkers Logger

File : logger.py

Brief : This file contains the definitions and functionalities for handling
        the debug log.
"""

import logging

logger = None
delimiter = "=================================================="
_category_number = 0
_test_number = 0
_current_category = None
_current_test = None
_test_exchanges = []


def log_use_case_category_header(category_name):
    """
    Logs the use case category header

    Args:
        category_name: The name of the category
    """
    global _category_number, _test_number, _current_category

    logger.info(delimiter)
    logger.info(delimiter)
    logger.info("{} Use Cases (Start)".format(category_name))
    logger.info(delimiter)
    logger.info(delimiter)
    _category_number += 1
    _test_number = 0
    _current_category = category_name
    print("{}. Performing {} use cases...".format(_category_number, category_name))


def log_use_case_category_footer(category_name):
    """
    Logs the use case category footer

    Args:
        category_name: The name of the category
    """
    logger.info(delimiter)
    logger.info(delimiter)
    logger.info("{} Use Cases (End)".format(category_name))
    logger.info(delimiter)
    logger.info(delimiter)
    print()


def log_use_case_test_header(category_name, test_name):
    """
    Logs the use case test header

    Args:
        category_name: The name of the category
        test_name: The name of the test
    """
    global _test_number, _current_test, _test_exchanges

    logger.info(delimiter)
    logger.info("{}: {} Test (Start)".format(category_name, test_name))
    logger.info(delimiter)
    _test_number += 1
    _current_test = test_name
    _test_exchanges = []
    print("{}.{} Running the {} test...".format(_category_number, _test_number, test_name))


def log_use_case_test_footer(category_name, test_name):
    """
    Logs the use case test footer

    Args:
        category_name: The name of the category
        test_name: The name of the test
    """
    logger.info(delimiter)
    logger.info("{}: {} Test (End)".format(category_name, test_name))
    logger.info(delimiter)
    print()
    rows = [("S#", "Method", "URL")]
    rows.extend(
        (
            "{}.{}.{}".format(_category_number, _test_number, call_number),
            exchange["method"],
            exchange["url"],
        )
        for call_number, exchange in enumerate(_test_exchanges, start=1)
    )
    widths = [max(len(row[index]) for row in rows) for index in range(3)]
    border = "+{}+{}+{}+".format(*("-" * (width + 2) for width in widths))
    print(border)
    for row in rows:
        print("|{}|{}|{}|".format(*(" {:<{}} ".format(value, width) for value, width in zip(row, widths))))
        print(border)
    print()


def log_api_call(exchange):
    """Records an API call for the currently running use case test."""
    _test_exchanges.append(exchange)
