# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

"""
Power Control Use Cases

File : power_control.py

Brief : This file contains the definitions and functionalities for testing
        use cases for power control
"""

import logging
import redfish
import redfish_utilities
import time

from redfish_use_case_checkers.system_under_test import SystemUnderTest
from redfish_use_case_checkers import logger

CAT_NAME = "Power Control"
TEST_SYSTEM_COUNT = (
    "System Count",
    "Verifies the system list is not empty",
    "Locates the ComputerSystemCollection resource and performs GET on all members.",
)
TEST_RESET_TYPE = (
    "Reset Type",
    "Verifies the each system reports supported reset types",
    "Inspects the Reset action for each system for the supported reset types.",
)
TEST_RESET_OPERATION = (
    "Reset Operation",
    "Verifies that a system can be reset",
    "Performs a POST operation on the Reset action on the ComputerSystem resource.  Performs a GET on the ComputerSystem resource and verifies it's in the desired power state.",
)
TEST_LIST = [TEST_SYSTEM_COUNT, TEST_RESET_TYPE, TEST_RESET_OPERATION]


def use_cases(sut: SystemUnderTest):
    """
    Performs the use cases for boot override

    Args:
        sut: The system under test
    """

    logger.log_use_case_category_header(CAT_NAME)

    # Set initial results
    sut.add_results_category(CAT_NAME, TEST_LIST)

    # Check that there is a system collection
    if "Systems" not in sut.service_root:
        for test in TEST_LIST:
            sut.add_test_result(CAT_NAME, test[0], "", "SKIP", "Service does not contain a system collection.")
        logger.log_use_case_category_footer(CAT_NAME)
        return

    # Go through the test cases
    test_systems = power_test_system_count(sut)
    reset_capabilities = power_test_reset_type(sut, test_systems)
    power_test_reset_operation(sut, test_systems, reset_capabilities)

    logger.log_use_case_category_footer(CAT_NAME)


def power_test_system_count(sut: SystemUnderTest):
    """
    Performs the system count test

    Args:
        sut: The system under test

    Returns:
        An array of systems found
    """

    test_name = TEST_SYSTEM_COUNT[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)
    systems = []
    system_ids = []

    # Get the list of systems
    operation = "Counting the members of the system collection"
    logger.logger.info(operation)
    try:
        system_ids = redfish_utilities.get_system_ids(sut.session)
        if len(system_ids) == 0:
            sut.add_test_result(CAT_NAME, test_name, operation, "FAIL", "No systems were found.")
        else:
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
    except Exception as err:
        sut.add_test_result(CAT_NAME, test_name, operation, "FAIL", "Failed to get the system list ({}).".format(err))

    # Get each member of the system collection
    for member in system_ids:
        operation = "Getting system '{}'".format(member)
        logger.logger.info(operation)
        try:
            system_resp = redfish_utilities.get_system(sut.session, member)
            systems.append(system_resp.dict)
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
        except Exception as err:
            sut.add_test_result(
                CAT_NAME, test_name, operation, "FAIL", "Failed to get the system '{}' ({}).".format(member, err)
            )

    logger.log_use_case_test_footer(CAT_NAME, test_name)
    return systems


def power_test_reset_type(sut: SystemUnderTest, systems: list):
    """
    Performs the reset type test

    Args:
        sut: The system under test
        systems: The systems to test

    Returns:
        A dictionary of reset capabilities for each system
    """

    test_name = TEST_RESET_TYPE[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)
    reset_capabilities = {}

    for system in systems:
        operation = "Getting supported reset types for system '{}'".format(system["Id"])
        logger.logger.info(operation)

        # Skip if the system does not support the reset action
        if "Actions" not in system:
            sut.add_test_result(
                CAT_NAME, test_name, operation, "SKIP", "System '{}' does not support any actions.".format(system["Id"])
            )
            continue
        if "#ComputerSystem.Reset" not in system["Actions"]:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "System '{}' does not support the 'Reset' action.".format(system["Id"]),
            )
            continue

        # Get the reset types
        try:
            reset_types = None
            reset_uri, reset_params = redfish_utilities.get_system_reset_info(sut.session, system["Id"])
            for param in reset_params:
                if param["Name"] == "ResetType":
                    reset_types = param["AllowableValues"]
                    reset_capabilities[system["Id"]] = reset_types
            if reset_types is None:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAILWARN",
                    "System '{}' does not report supported reset types.".format(system["Id"]),
                )
            else:
                sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
        except Exception as err:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "Failed to get the reset types supported for system '{}' ({}).".format(system["Id"], err),
            )

    logger.log_use_case_test_footer(CAT_NAME, test_name)
    return reset_capabilities


def power_test_reset_operation(sut: SystemUnderTest, systems: list, reset_capabilities: dict):
    """
    Performs the reset operation test

    Args:
        sut: The system under test
        systems: The systems to test
        reset_capabilities: The reset capabilities for each system
    """

    test_name = TEST_RESET_OPERATION[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)
    reset_types = ["ForceOff", "ForceRestart", "PowerCycle", "On", "ForceOn"]

    # Test each reset type
    for reset_type in reset_types:
        reset_success = {}

        # Reset each system
        for system in systems:
            operation = "Performing the reset action with the reset type '{}' for system '{}'".format(
                reset_type, system["Id"]
            )
            logger.logger.info(operation)

            # Skip if the system does not support the reset action or shows reset capabilities
            if system["Id"] not in reset_capabilities:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "SKIP",
                    "System '{}' does not support the 'Reset' action or does not show supported reset types.".format(
                        system["Id"]
                    ),
                )
                continue

            # Skip if the system does not support the reset type
            if reset_type not in reset_capabilities[system["Id"]]:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "SKIP",
                    "System '{}' does not support the reset action with reset type '{}'.".format(
                        system["Id"], reset_type
                    ),
                )
                continue

            # Perform the reset
            reset_success[system["Id"]] = False
            try:
                response = redfish_utilities.system_reset(sut.session, system["Id"], reset_type)
                response = redfish_utilities.poll_task_monitor(sut.session, response, silent=True)
                redfish_utilities.verify_response(response)
                sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
                reset_success[system["Id"]] = True
            except Exception as err:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAILWARN",
                    "Failed to reset system '{}' ({}).".format(system["Id"], err),
                )

        # Wait for all systems to reset
        time.sleep(10)

        # Monitor each system to ensure it's in the desired power state
        for system in systems:
            if system["Id"] not in reset_success:
                # Silently skip systems we already marked as skipped from the previous step
                continue

            operation = "Monitoring the power state of system '{}'".format(system["Id"])
            logger.logger.info(operation)

            # Skip if the system does not support reporting the power state
            if reset_success[system["Id"]] == False:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "SKIP",
                    "System '{}' failed the reset action with reset type '{}'.".format(system["Id"], reset_type),
                )
                continue

            # Skip if the system does not support reporting the power state
            if "PowerState" not in system:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "SKIP",
                    "System '{}' does not support the 'PowerState' property.".format(system["Id"]),
                )
                continue

            # Monitor the system enter the desired power state
            expected_power_state = "On"
            if reset_type == "ForceOff":
                expected_power_state = "Off"
            try:
                # Poll the power state for up to 50 seconds
                for i in range(0, 10):
                    logger.logger.debug("Monitoring check {}".format(i))
                    system_info = redfish_utilities.get_system(sut.session, system["Id"])
                    if system_info.dict["PowerState"] == expected_power_state:
                        break
                    time.sleep(5)

                logger.logger.info(
                    "Finished monitoring the power state for system '{}'; 'PowerState' contains '{}'".format(
                        system["Id"], system_info.dict["PowerState"]
                    )
                )

                if system_info.dict["PowerState"] != expected_power_state:
                    sut.add_test_result(
                        CAT_NAME,
                        test_name,
                        operation,
                        "FAIL",
                        "System '{}' did not transition to the '{}' power state after performing a reset of type '{}'.".format(
                            system["Id"], expected_power_state, reset_type
                        ),
                    )
                else:
                    sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
            except Exception as err:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAIL",
                    "Failed to monitor the power state for system '{}' ({}).".format(system["Id"], err),
                )

    logger.log_use_case_test_footer(CAT_NAME, test_name)
