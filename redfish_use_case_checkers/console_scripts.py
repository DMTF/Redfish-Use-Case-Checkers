# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

"""
Redfish Use Case Checkers Console Scripts

File : console_scripts.py

Brief : This file contains the definitions and functionalities for invoking
        the use case checkers.
"""

import argparse
import colorama
import logging
import redfish
import sys
from datetime import datetime
from pathlib import Path

from redfish_use_case_checkers.system_under_test import SystemUnderTest
from redfish_use_case_checkers import account_management
from redfish_use_case_checkers import boot_override
from redfish_use_case_checkers import logger
from redfish_use_case_checkers import manager_ethernet_interfaces
from redfish_use_case_checkers import power_control
from redfish_use_case_checkers import report

tool_version = "2.0.3"


def main():
    """
    Entry point for the use case checkers
    """

    # Get the input arguments
    argget = argparse.ArgumentParser(description="Validate Redfish services against use cases")
    argget.add_argument("--user", "-u", type=str, required=True, help="The username for authentication")
    argget.add_argument("--password", "-p", type=str, required=True, help="The password for authentication")
    argget.add_argument(
        "--rhost", "-r", type=str, required=True, help="The address of the Redfish service (with scheme)"
    )
    argget.add_argument(
        "--report-dir",
        type=str,
        default="reports",
        help="The directory for generated report files (default: 'reports')",
    )
    argget.add_argument(
        "--relaxed",
        action="store_true",
        help="Allows for some failures to be logged as warnings; useful if the criteria is to meet the literal 'shall' statements in the specification.",
    )
    argget.add_argument(
        "--test-list",
        nargs="*",
        choices=["AccountManagement", "PowerControl", "BootOverride", "ManagerEthernetInterfaces"],
        help="Selects specific tests to perform instead of running the entire test suite."
    )
    argget.add_argument(
        "--debugging",
        action="store_true",
        help="Controls the verbosity of the debugging output; if not specified only INFO and higher are logged.",
    )
    args = argget.parse_args()

    # Create report directory if needed
    report_dir = Path(args.report_dir)
    if not report_dir.is_dir():
        report_dir.mkdir(parents=True)

    # Get the current time for report files
    test_time = datetime.now()

    # Set the logging level
    log_level = logging.INFO
    if args.debugging:
        log_level = logging.DEBUG
    log_file = report_dir / "RedfishUseCaseCheckersDebug_{}.log".format(test_time.strftime("%m_%d_%Y_%H%M%S"))
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logger.logger = redfish.redfish_logger(log_file, log_format, log_level)
    logger.logger.info("Redfish Use Case Checkers")
    logger.logger.info("Version: {}".format(tool_version))
    logger.logger.info("System: {}".format(args.rhost))
    logger.logger.info("User: {}".format(args.user))
    print("Redfish Use Case Checkers, Version {}".format(tool_version))
    print()

    # Set up the system
    sut = SystemUnderTest(args.rhost, args.user, args.password, args.relaxed)

    # Run the tests
    if args.test_list is None or "AccountManagement" in args.test_list:
        account_management.use_cases(sut)
    if args.test_list is None or "PowerControl" in args.test_list:
        power_control.use_cases(sut)
    if args.test_list is None or "BootOverride" in args.test_list:
        boot_override.use_cases(sut)
    if args.test_list is None or "ManagerEthernetInterfaces" in args.test_list:
        manager_ethernet_interfaces.use_cases(sut)

    # Log out
    sut.logout()

    print_summary(sut)
    results_file = report.html_report(sut, report_dir, test_time, tool_version)
    print("HTML Report: {}".format(results_file))
    print("Debug Log: {}".format(log_file))

    # Exit with status 1 if there are any failures; 0 otherwise
    sys.exit(int(sut.fail_count > 0))


def summary_format(result, result_count):
    """
    Returns a color-coded result format

    Args:
        result: The type of result
        result_count: The number of results for that type
    """
    color_map = {
        "PASS": (colorama.Fore.GREEN, colorama.Style.RESET_ALL),
        "WARN": (colorama.Fore.YELLOW, colorama.Style.RESET_ALL),
        "FAIL": (colorama.Fore.RED, colorama.Style.RESET_ALL),
    }
    start, end = ("", "")
    if result_count:
        start, end = color_map.get(result, ("", ""))
    return start, result_count, end


def print_summary(sut):
    """
    Prints a stylized summary of the test results

    Args:
        sut: The system under test
    """
    colorama.init()
    pass_start, passed, pass_end = summary_format("PASS", sut.pass_count)
    warn_start, warned, warn_end = summary_format("WARN", sut.warn_count)
    fail_start, failed, fail_end = summary_format("FAIL", sut.fail_count)
    no_test_start, not_tested, no_test_end = summary_format("SKIP", sut.skip_count)
    print(
        "Summary - %sPASS: %s%s, %sWARN: %s%s, %sFAIL: %s%s, %sNOT TESTED: %s%s"
        % (
            pass_start,
            passed,
            pass_end,
            warn_start,
            warned,
            warn_end,
            fail_start,
            failed,
            fail_end,
            no_test_start,
            not_tested,
            no_test_end,
        )
    )
    colorama.deinit()
