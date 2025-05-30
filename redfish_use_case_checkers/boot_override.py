# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

"""
Boot Override Use Cases

File : boot_override.py

Brief : This file contains the definitions and functionalities for testing
        use cases for boot override
"""

import logging
import redfish
import redfish_utilities
import time

from redfish_use_case_checkers.system_under_test import SystemUnderTest
from redfish_use_case_checkers import logger

CAT_NAME = "Boot Override"
TEST_SYSTEM_COUNT = (
    "System Count",
    "Verifies the system list is not empty",
    "Locates the ComputerSystemCollection resource and performs GET on all members.",
)
TEST_BOOT_OVERRIDE_CHECK = (
    "Boot Override Check",
    "Verifies that a system contains the boot override object",
    "Verifies the Boot property is present along with its boot override properties.",
)
TEST_CONTINUOUS_BOOT_SETTING = (
    "Continuous Boot Override",
    "Verifies the boot override supports the 'continuous' mode",
    "Performs a PATCH on the ComputerSystem resource to set the boot override to 'continuous' mode.  Performs a GET on the ComputerSystem resource to verify the requested settings were applied.",
)
TEST_ONE_TIME_BOOT_SETTING = (
    "One-Time Boot Override",
    "Verifies the boot override supports the 'one-time' mode",
    "Performs a PATCH on the ComputerSystem resource to set the boot override to 'one-time' mode.  Performs a GET on the ComputerSystem resource to verify the requested settings were applied.",
)
TEST_ONE_TIME_BOOT_CHECK = (
    "One-Time Boot Override Check",
    "Verifies the one-time boot override is performed",
    "Performs a POST to the Reset action on the ComputerSystem resource.  Monitors the boot override mode transitions back to 'disabled' after the reset.",
)
TEST_DISABLE_BOOT_SETTING = (
    "Disable Boot Override",
    "Verifies the boot override can be disabled",
    "Performs a PATCH on the ComputerSystem resource to set the boot override to 'disabled' mode.  Performs a GET on the ComputerSystem resource to verify the requested settings were applied.",
)
TEST_LIST = [
    TEST_SYSTEM_COUNT,
    TEST_BOOT_OVERRIDE_CHECK,
    TEST_CONTINUOUS_BOOT_SETTING,
    TEST_ONE_TIME_BOOT_SETTING,
    TEST_ONE_TIME_BOOT_CHECK,
    TEST_DISABLE_BOOT_SETTING,
]


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
    test_systems = boot_test_system_count(sut)
    boot_params = boot_test_boot_check(sut, test_systems)
    boot_test_continuous_boot_settings(sut, test_systems, boot_params)
    one_time_systems = boot_test_one_time_boot_settings(sut, test_systems, boot_params)
    boot_test_one_time_boot_check(sut, test_systems, one_time_systems)
    boot_test_disable_boot_settings(sut, test_systems, boot_params)

    logger.log_use_case_category_footer(CAT_NAME)


def boot_test_system_count(sut: SystemUnderTest):
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


def boot_test_boot_check(sut: SystemUnderTest, systems: list):
    """
    Performs the boot check test

    Args:
        sut: The system under test
        systems: The systems to test

    Returns:
        An array of boot parameters for future tests
    """

    test_name = TEST_BOOT_OVERRIDE_CHECK[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)
    boot_override_params = []

    # Skip the test if there are no systems
    if len(systems) == 0:
        sut.add_test_result(CAT_NAME, test_name, "", "SKIP", "System collection is empty.")
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return boot_override_params

    # Inspect the boot object for each system
    for system in systems:
        # Check if the system has a boot object
        operation = "Checking for the 'Boot' property in system '{}'".format(system["Id"])
        logger.logger.info(operation)
        if "Boot" not in system:
            # No boot object; skip
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "System '{}' does not contain the 'Boot' property.".format(system["Id"]),
            )
            boot_override_params.append(None)
            continue
        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

        # Check if the system has boot override properties
        operation = "Checking for the 'BootSourceOverrideTarget' and 'BootSourceOverrideEnabled' properties in system '{}'".format(
            system["Id"]
        )
        logger.logger.info(operation)
        if "BootSourceOverrideTarget" not in system["Boot"] and "BootSourceOverrideEnabled" not in system["Boot"]:
            # Both BootSourceOverrideTarget and BootSourceOverrideEnabled properties not present; skip
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "System '{}' does not contain the boot override properties.".format(system["Id"]),
            )
            boot_override_params.append(None)
            continue
        elif "BootSourceOverrideTarget" not in system["Boot"] or "BootSourceOverrideEnabled" not in system["Boot"]:
            # Only one of the properties is present; boot override is not useable without both
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "System '{}' contains 'BootSourceOverrideTarget' or 'BootSourceOverrideEnabled', but not both.".format(
                    system["Id"]
                ),
            )
            boot_override_params.append(None)
            continue
        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

        # Check for the allowable values properties
        for allow_prop in ["BootSourceOverrideTarget", "BootSourceOverrideEnabled"]:
            operation = "Checking for the '{}@Redfish.AllowableValues' property in system '{}'".format(
                allow_prop, system["Id"]
            )
            logger.logger.info(operation)
            if allow_prop + "@Redfish.AllowableValues" not in system["Boot"]:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "WARN",
                    "System '{}' does not contain '{}'@Redfish.AllowableValues.".format(system["Id"], allow_prop),
                )
            else:
                sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

        # Cache the allowable boot parameters
        # If the allowable values term is not present, assume it supports PXE, Continuous, and Once
        boot_params = {}
        boot_params["PXE"] = (
            True if "Pxe" in system["Boot"].get("BootSourceOverrideTarget@Redfish.AllowableValues", ["Pxe"]) else False
        )
        boot_params["USB"] = (
            True if "USB" in system["Boot"].get("BootSourceOverrideTarget@Redfish.AllowableValues", []) else False
        )
        boot_params["Continuous"] = (
            True
            if "Continuous" in system["Boot"].get("BootSourceOverrideEnabled@Redfish.AllowableValues", ["Continuous"])
            else False
        )
        boot_params["Once"] = (
            True
            if "Once" in system["Boot"].get("BootSourceOverrideEnabled@Redfish.AllowableValues", ["Once"])
            else False
        )
        boot_override_params.append(boot_params)

        # Check if the boot object contains other properties as needed by the allowable boot override targets
        boot_override_targets = ["UefiTarget", "UefiBootNext"]
        boot_override_properties = ["UefiTargetBootSourceOverride", "BootNext"]
        for target, prop in zip(boot_override_targets, boot_override_properties):
            operation = "Checking that the 'Boot' property in system '{}' contains the '{}' property".format(
                system["Id"], target
            )
            logger.logger.info(operation)
            if "BootSourceOverrideTarget@Redfish.AllowableValues" not in system["Boot"]:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "SKIP",
                    "System '{}' does not contain 'BootSourceOverrideTarget@Redfish.AllowableValues'.".format(
                        system["Id"]
                    ),
                )
                continue
            if target in system["Boot"]["BootSourceOverrideTarget@Redfish.AllowableValues"]:
                if prop not in system["Boot"]:
                    sut.add_test_result(
                        CAT_NAME,
                        test_name,
                        operation,
                        "FAIL",
                        "System '{}' supports boot override to '{}' but does not contain '{}'.".format(
                            system["Id"], target, prop
                        ),
                    )
                else:
                    sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
            else:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "SKIP",
                    "System '{}' does not support boot override to '{}'.".format(system["Id"], target),
                )

    logger.log_use_case_test_footer(CAT_NAME, test_name)
    return boot_override_params


def boot_test_continuous_boot_settings(sut: SystemUnderTest, systems: list, boot_override_params: list):
    """
    Performs the continuous boot settings test

    Args:
        sut: The system under test
        systems: The systems to test
        boot_override_params: The boot override parameters for each system
    """

    test_name = TEST_CONTINUOUS_BOOT_SETTING[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Skip the test if there are no systems
    if len(systems) == 0:
        sut.add_test_result(CAT_NAME, test_name, "", "SKIP", "System collection is empty.")
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Try to get the boot override object for each system
    for system, boot_param in zip(systems, boot_override_params):
        operation = "Setting boot override to 'continuous' mode for system '{}'".format(system["Id"])
        logger.logger.info(operation)
        if boot_param is None:
            # No boot override; skip
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "System '{}' does not support boot override.".format(system["Id"]),
            )
            continue
        if boot_param["Continuous"] is False:
            # No continuous boot; skip
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "System '{}' does not support 'continuous' boot override.".format(system["Id"]),
            )
            continue

        # Determine the boot path to test
        boot_path = None
        boot_mode = "Continuous"
        if boot_param["PXE"]:
            boot_path = "Pxe"
        elif boot_param["USB"]:
            boot_path = "Usb"
        if boot_path is None:
            # No PXE or USB; skip
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "System '{}' does not support PXE or USB boot override.".format(system["Id"]),
            )
            continue

        # Set the boot override
        try:
            redfish_utilities.set_system_boot(
                sut.session, system_id=system["Id"], ov_target=boot_path, ov_enabled=boot_mode
            )
            boot_obj = redfish_utilities.get_system_boot(sut.session, system["Id"])
            if boot_obj["BootSourceOverrideTarget"] != boot_path and boot_obj["BootSourceOverrideEnabled"] != boot_mode:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAIL",
                    "'Boot' property contains '{}'/'{}' instead of '{}'/'{}' after PATCH operation.".format(
                        boot_obj["BootSourceOverrideTarget"],
                        boot_obj["BootSourceOverrideEnabled"],
                        boot_path,
                        boot_mode,
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
                "Failed to set boot override for system '{}' to '{}'/'{}'.".format(system["Id"], boot_path, boot_mode),
            )

    logger.log_use_case_test_footer(CAT_NAME, test_name)


def boot_test_one_time_boot_settings(sut: SystemUnderTest, systems: list, boot_override_params: list):
    """
    Performs the once-time boot override settings test

    Args:
        sut: The system under test
        systems: The systems to test
        boot_override_params: The boot override parameters for each system

    Returns:
        An array of the systems where the boot override was successfully set
    """

    test_name = TEST_ONE_TIME_BOOT_SETTING[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)
    one_time_systems = []

    # Skip the test if there are no systems
    if len(systems) == 0:
        sut.add_test_result(CAT_NAME, test_name, "", "SKIP", "System collection is empty.")
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Try to get the boot override object for each system
    for system, boot_param in zip(systems, boot_override_params):
        operation = "Setting boot override to 'one-time' mode for system '{}'".format(system["Id"])
        logger.logger.info(operation)
        if boot_param is None:
            # No boot override; skip
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "System '{}' does not support boot override.".format(system["Id"]),
            )
            continue
        if boot_param["Once"] is False:
            # No one-time boot; skip
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "System '{}' does not support 'one-time' boot override.".format(system["Id"]),
            )
            continue

        # Determine the boot path to test
        boot_path = None
        boot_mode = "Once"
        if boot_param["PXE"]:
            boot_path = "Pxe"
        elif boot_param["USB"]:
            boot_path = "Usb"
        if boot_path is None:
            # No PXE or USB; skip
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "System '{}' does not support PXE or USB boot override.".format(system["Id"]),
            )
            continue

        # Set the boot override
        try:
            redfish_utilities.set_system_boot(
                sut.session, system_id=system["Id"], ov_target=boot_path, ov_enabled=boot_mode
            )
            boot_obj = redfish_utilities.get_system_boot(sut.session, system["Id"])
            if boot_obj["BootSourceOverrideTarget"] != boot_path and boot_obj["BootSourceOverrideEnabled"] != boot_mode:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAIL",
                    "'Boot' property contains '{}'/'{}' instead of '{}'/'{}' after PATCH operation.".format(
                        boot_obj["BootSourceOverrideTarget"],
                        boot_obj["BootSourceOverrideEnabled"],
                        boot_path,
                        boot_mode,
                    ),
                )
            else:
                sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
                one_time_systems.append(system["Id"])
        except Exception as err:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "Failed to set boot override for system '{}' to '{}'/'{}'.".format(system["Id"], boot_path, boot_mode),
            )

    logger.log_use_case_test_footer(CAT_NAME, test_name)
    return one_time_systems


def boot_test_one_time_boot_check(sut: SystemUnderTest, systems: list, check_systems: list):
    """
    Performs the one-time boot override check test

    Args:
        sut: The system under test
        systems: The systems to test
        check_systems: Indicates which systems to check
    """

    test_name = TEST_ONE_TIME_BOOT_CHECK[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Skip the test if there are no systems
    if len(systems) == 0:
        sut.add_test_result(CAT_NAME, test_name, "", "SKIP", "System collection is empty.")
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Try to get the boot override object for each system
    for system in systems:
        operation = "Performing one-time boot for system '{}'".format(system["Id"])
        logger.logger.info(operation)
        if system["Id"] not in check_systems:
            # Did not set the boot override; skip
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "System '{}' was not set to 'one-time' in the previous test.".format(system["Id"]),
            )
            continue

        # Reset the system
        operation = "Resetting system '{}'".format(system["Id"])
        logger.logger.info(operation)
        reset_success = False
        try:
            response = redfish_utilities.system_reset(sut.session, system["Id"])
            response = redfish_utilities.poll_task_monitor(sut.session, response, silent=True)
            redfish_utilities.verify_response(response)
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
            reset_success = True
        except Exception as err:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAILWARN",
                "Failed to reset system '{}' ({}).".format(system["Id"], err),
            )

        # Monitor the system to go back to None
        operation = "Monitoring the boot progress for system '{}'".format(system["Id"])
        logger.logger.info(operation)
        if reset_success:
            try:
                # Poll the boot object for up to 600 seconds
                for i in range(0, 60):
                    logger.logger.debug("Monitoring check {}".format(i))
                    time.sleep(10)
                    boot_obj = redfish_utilities.get_system_boot(sut.session, system["Id"])
                    if boot_obj["BootSourceOverrideEnabled"] == "Disabled":
                        break

                logger.logger.info(
                    "Finished monitoring the boot progress for system '{}'; 'BootSourceOverrideEnabled' contains '{}'".format(
                        system["Id"], boot_obj["BootSourceOverrideEnabled"]
                    )
                )

                # Log the results based on what the last reading was
                if boot_obj["BootSourceOverrideEnabled"] == "Disabled":
                    logger.logger.info("System '{}' transitioned back to 'Disabled'".format(system["Id"]))
                    sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
                else:
                    sut.add_test_result(
                        CAT_NAME,
                        test_name,
                        operation,
                        "FAIL",
                        "Boot override for system '{}' did not transition back to 'Disabled' after reset.".format(
                            system["Id"]
                        ),
                    )
            except Exception as err:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAIL",
                    "Failed to monitor the boot progress for system '{}' ({}).".format(system["Id"], err),
                )
        else:
            sut.add_test_result(
                CAT_NAME, test_name, operation, "SKIP", "System '{}' was not reset successfully.".format(system["Id"])
            )

    logger.log_use_case_test_footer(CAT_NAME, test_name)


def boot_test_disable_boot_settings(sut: SystemUnderTest, systems: list, boot_override_params: list):
    """
    Performs the disable boot override settings test

    Args:
        sut: The system under test
        systems: The systems to test
        boot_override_params: The boot override parameters for each system
    """

    test_name = TEST_DISABLE_BOOT_SETTING[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Skip the test if there are no systems
    if len(systems) == 0:
        sut.add_test_result(CAT_NAME, test_name, "", "SKIP", "System collection is empty.")
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Try to get the boot override object for each system
    for system, boot_param in zip(systems, boot_override_params):
        operation = "Setting boot override to 'disabled' mode for system '{}'".format(system["Id"])
        logger.logger.info(operation)
        if boot_param is None:
            # No boot override; skip
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "System '{}' does not support boot override.".format(system["Id"]),
            )
            continue

        # Disable the boot override
        boot_path = "None"
        boot_mode = "Disabled"
        try:
            redfish_utilities.set_system_boot(
                sut.session, system_id=system["Id"], ov_target=boot_path, ov_enabled=boot_mode
            )
            boot_obj = redfish_utilities.get_system_boot(sut.session, system["Id"])
            if boot_obj["BootSourceOverrideTarget"] != boot_path and boot_obj["BootSourceOverrideEnabled"] != boot_mode:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAIL",
                    "'Boot' property contains '{}'/'{}' instead of '{}'/'{}' after PATCH operation.".format(
                        boot_obj["BootSourceOverrideTarget"],
                        boot_obj["BootSourceOverrideEnabled"],
                        boot_path,
                        boot_mode,
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
                "Failed to set boot override for system '{}' to '{}'/'{}'.".format(system["Id"], boot_path, boot_mode),
            )

    logger.log_use_case_test_footer(CAT_NAME, test_name)
