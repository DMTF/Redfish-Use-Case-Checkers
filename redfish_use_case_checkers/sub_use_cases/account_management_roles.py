# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

"""Account Management role sub-use cases."""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import redfish
import redfish_utilities

from redfish_use_case_checkers import logger
from redfish_use_case_checkers import report
from redfish_use_case_checkers.system_under_test import SystemUnderTest


EXPECTED_PRIVILEGES = {
    "Administrator": {
        "Login",
        "ConfigureManager",
        "ConfigureUsers",
        "ConfigureSelf",
        "ConfigureComponents",
    },
    "Operator": {"Login", "ConfigureSelf", "ConfigureComponents"},
    "ReadOnly": {"Login", "ConfigureSelf"},
}

CAT_NAME = "Account Management"
TEST_ROLE_ASSIGNED_PRIVILEGES = (
    "Role Assigned Privileges",
    "Verifies the assigned privileges of the predefined roles",
    "Reads the RoleCollection and verifies the AssignedPrivileges values for the Administrator, Operator, and ReadOnly roles.",
)


def check_assigned_privileges(sut: SystemUnderTest, category_name: str, test_name: str):
    """Verifies the assigned privileges of the standard predefined roles."""

    operation = "Locating the role collection"
    logger.logger.info(operation)
    try:
        account_service_uri = sut.service_root["AccountService"]["@odata.id"]
        account_service = sut.session.get(account_service_uri)
        redfish_utilities.verify_response(account_service)
        role_collection_uri = account_service.dict["Roles"]["@odata.id"]
        role_collection = sut.session.get(role_collection_uri)
        redfish_utilities.verify_response(role_collection)
    except Exception as err:
        sut.add_test_result(
            category_name,
            test_name,
            operation,
            "FAIL",
            "Failed to get the role collection ({}).".format(err),
        )
        return

    roles = {}
    for member in role_collection.dict.get("Members", []):
        if not isinstance(member, dict) or "@odata.id" not in member:
            continue
        try:
            role = sut.session.get(member["@odata.id"])
            redfish_utilities.verify_response(role)
            role_id = role.dict.get("RoleId")
            if role_id:
                roles[role_id] = role.dict
        except Exception as err:
            operation = "Getting role '{}'".format(member["@odata.id"])
            sut.add_test_result(
                category_name,
                test_name,
                operation,
                "FAIL",
                "Failed to get role ({}).".format(err),
            )

    for role_name, expected_privileges in EXPECTED_PRIVILEGES.items():
        operation = "Checking assigned privileges for '{}'".format(role_name)
        logger.logger.info(operation)
        if role_name not in roles:
            sut.add_test_result(
                category_name,
                test_name,
                operation,
                "FAIL",
                "Role '{}' is not present in the role collection.".format(role_name),
            )
            continue

        assigned_privileges = roles[role_name].get("AssignedPrivileges")
        if not isinstance(assigned_privileges, list):
            sut.add_test_result(
                category_name,
                test_name,
                operation,
                "FAIL",
                "Role '{}' does not contain an AssignedPrivileges array.".format(role_name),
            )
            continue

        actual_privileges = set(assigned_privileges)
        if actual_privileges == expected_privileges and len(assigned_privileges) == len(actual_privileges):
            sut.add_test_result(category_name, test_name, operation, "PASS")
        else:
            sut.add_test_result(
                category_name,
                test_name,
                operation,
                "FAIL",
                "Role '{}' has AssignedPrivileges {}; expected {}.".format(
                    role_name,
                    sorted(actual_privileges),
                    sorted(expected_privileges),
                ),
            )


def main():
    """Runs only the predefined role assigned-privileges check."""

    argget = argparse.ArgumentParser(description="Verify Redfish predefined role privileges")
    argget.add_argument("--user", "-u", type=str, required=True, help="The username for authentication")
    argget.add_argument("--password", "-p", type=str, required=True, help="The password for authentication")
    argget.add_argument("--rhost", "-r", type=str, required=True, help="The address of the Redfish service (with scheme)")
    argget.add_argument("--report-dir", type=str, default="reports", help="The directory for generated report files")
    argget.add_argument("--relaxed", action="store_true", help="Treat relaxed failures as warnings")
    argget.add_argument("--debugging", action="store_true", help="Enable debug logging")
    args = argget.parse_args()

    test_time = datetime.now()
    report_dir = Path(args.report_dir) / test_time.strftime("%Y-%m-%d-%H%M%S")
    report_dir.mkdir(parents=True, exist_ok=True)
    log_level = logging.DEBUG if args.debugging else logging.INFO
    log_file = report_dir / "RedfishUseCaseCheckersDebug_{}.log".format(test_time.strftime("%m_%d_%Y_%H%M%S"))
    logger.logger = redfish.redfish_logger(
        log_file, "%(asctime)s - %(name)s - %(levelname)s - %(message)s", log_level
    )

    sut = SystemUnderTest(args.rhost, args.user, args.password, args.relaxed)
    sut.add_results_category(CAT_NAME, [TEST_ROLE_ASSIGNED_PRIVILEGES])
    logger.log_use_case_category_header(CAT_NAME)
    logger.log_use_case_test_header(CAT_NAME, TEST_ROLE_ASSIGNED_PRIVILEGES[0])
    check_assigned_privileges(sut, CAT_NAME, TEST_ROLE_ASSIGNED_PRIVILEGES[0])
    logger.log_use_case_test_footer(CAT_NAME, TEST_ROLE_ASSIGNED_PRIVILEGES[0])
    logger.log_use_case_category_footer(CAT_NAME)
    sut.logout()

    results_file = report.html_report(sut, report_dir, test_time, "2.1.0", vars(args))
    xlsx_file = report.xlsx_report(sut, report_dir, test_time, "2.1.0")
    print("HTML Report:  {}".format(results_file))
    print("Excel Report: {}".format(xlsx_file))
    print("Debug Log:    {}".format(log_file))
    sys.exit(int(sut.fail_count > 0))


if __name__ == "__main__":
    main()