# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

"""
Account Management Use Cases

File : account_management.py

Brief : This file contains the definitions and functionalities for testing
        use cases for account management
"""

import logging
import re
import redfish
import redfish_utilities

from redfish_use_case_checkers.system_under_test import SystemUnderTest
from redfish_use_case_checkers import logger

CAT_NAME = "Account Management"
TEST_USER_COUNT = (
    "User Count",
    "Verifies the user list is not empty",
    "Locates the ManagerAccountCollection resource and performs GET on all members.",
)
TEST_ADD_USER = (
    "Add User",
    "Verifies that a user can be added",
    "Performs a POST operation on the ManagerAccountCollection resource.  Performs a GET on the new ManagerAccount resource and verifies the new user matches the specified criteria.",
)
TEST_ENABLE_USER = (
    "Enable User",
    "Verifies that a user can be enabled",
    "Performs a PATCH operation on the ManagerAccount resource to enable the new user.  Performs a GET on the ManagerAccount resource and verifies the user account was enabled.",
)
TEST_CREDENTIAL_CHECK = (
    "Credential Check",
    "Verifies the credentials of the new user are correctly enforced",
    "Creates a new Redfish session with the new user account.  Attempts to read the members of the ManagerAccountCollection resource with the new session.",
)
TEST_CHANGE_ROLE = (
    "Change Role",
    "Verifies that user roles can be modified",
    "Performs PATCH operations on the ManagerAccount resource of the new account to change the role.  Performs a GET on the ManagerAccount resource and verifies the role was changed as requested.",
)
TEST_DELETE_USER = (
    "Delete User",
    "Verifies that a user can be deleted",
    "Performs a DELETE operation on the ManagerAccount resource of the new account.  Reads the members of the ManagerAccountCollection resource and verifies the user was deleted.",
)
TEST_LIST = [
    TEST_USER_COUNT,
    TEST_ADD_USER,
    TEST_ENABLE_USER,
    TEST_CREDENTIAL_CHECK,
    TEST_CHANGE_ROLE,
    TEST_DELETE_USER,
]


def use_cases(sut: SystemUnderTest):
    """
    Performs the use cases for account management

    Args:
        sut: The system under test
    """

    logger.log_use_case_category_header(CAT_NAME)

    # Set initial results
    sut.add_results_category(CAT_NAME, TEST_LIST)

    # Check that there is an account service
    if "AccountService" not in sut.service_root:
        for test in TEST_LIST:
            sut.add_test_result(CAT_NAME, test[0], "", "SKIP", "Service does not contain an account service.")
        logger.log_use_case_category_footer(CAT_NAME)
        return

    # Let tasks for account operations be handled internally
    redfish_utilities.config.__auto_task_handling__ = True

    # Go through the test cases
    test_username = acc_test_user_count(sut)
    user_added, test_password = acc_test_add_user(sut, test_username)
    acc_test_enable_user(sut, user_added, test_username)
    acc_test_credential_check(sut, user_added, test_username, test_password)
    acc_test_change_role(sut, user_added, test_username)
    acc_test_delete_user(sut, user_added, test_username)
    logger.log_use_case_category_footer(CAT_NAME)


def verify_user(context, username, role=None, enabled=None):
    """
    Checks that a given user is in the user list with a certain role

    Args:
        context: The Redfish client object with an open session
        username: The name of the user to check
        role: The role for the user
        enabled: The enabled state for the user

    Returns:
        True if a match is found, false otherwise
    """
    user_list = redfish_utilities.get_users(context)
    for user in user_list:
        if user["UserName"] == username:
            if role is not None and user["RoleId"] != role:
                return False
            if enabled is not None and user["Enabled"] != enabled:
                return False
            return True

    return False


def acc_test_user_count(sut: SystemUnderTest):
    """
    Performs the user count test

    Args:
        sut: The system under test

    Returns:
        The username for testing
    """

    test_name = TEST_USER_COUNT[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)
    usernames = []
    operation = "Counting the members of the account collection"
    logger.logger.info(operation)

    # Get the list of current users
    try:
        user_list = redfish_utilities.get_users(sut.session)
        for user in user_list:
            usernames.append(user["UserName"])
        user_count = len(user_list)
        if user_count == 0:
            sut.add_test_result(CAT_NAME, test_name, operation, "FAIL", "No users were found.")
        else:
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
    except Exception as err:
        sut.add_test_result(CAT_NAME, test_name, operation, "FAIL", "Failed to get the user list ({}).".format(err))

    # Determine a username for testing
    for x in range(1000):
        test_username = "testuser" + str(x)
        if test_username not in usernames:
            break

    logger.log_use_case_test_footer(CAT_NAME, test_name)
    return test_username


def acc_test_add_user(sut: SystemUnderTest, username: str):
    """
    Performs the add user test

    Args:
        sut: The system under test
        username: The username for testing

    Returns:
        An indication if the test user was added
        The password for testing
    """

    test_name = TEST_ADD_USER[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)
    user_added = False
    test_passwords = ["hUPgd9Z4", "7jIl3dn!kd0Fql", "m5Ljed3!n0olvdS*m0kmWER15!"]

    # Create a new user
    last_error = ""
    operation = "Creating new user '{}' as 'Administrator'".format(username)
    logger.logger.info(operation)
    for x in range(3):
        # Try different passwords in case there are password requirements that we cannot detect
        try:
            test_password = test_passwords[x]
            redfish_utilities.add_user(sut.session, username, test_password, "Administrator")
            user_added = True
            break
        except Exception as err:
            last_error = err
    if not user_added:
        sut.add_test_result(
            CAT_NAME, test_name, operation, "FAIL", "Failed to create user '{}' ({}).".format(username, last_error)
        )
    else:
        # Get the list of current users to verify the new user was added
        if verify_user(sut.session, username, role="Administrator"):
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
        else:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "Failed to find user '{}' with the role 'Administrator' after successful POST.".format(username),
            )

    logger.log_use_case_test_footer(CAT_NAME, test_name)
    return user_added, test_password


def acc_test_enable_user(sut: SystemUnderTest, user_added: bool, username: str):
    """
    Performs the enable user test

    Args:
        sut: The system under test
        user_added: Indicates if the test user was added
        username: The username for testing
    """

    test_name = TEST_ENABLE_USER[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Skip the test if the test user was not added
    if not user_added:
        sut.add_test_result(
            CAT_NAME,
            test_name,
            "",
            "SKIP",
            "Failure of the '{}' test prevents performing this test.".format(TEST_ADD_USER[0]),
        )
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Check if the user needs to be enabled
    operation = "Enabling user '{}'".format(username)
    logger.logger.info(operation)
    try:
        if verify_user(sut.session, username, enabled=False):
            redfish_utilities.modify_user(sut.session, username, new_enabled=True)
            if verify_user(sut.session, username, enabled=True):
                sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
            else:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAIL",
                    "User '{}' not enabled after successful PATCH.".format(username),
                )
        else:
            sut.add_test_result(
                CAT_NAME, test_name, operation, "SKIP", "User '{}' already enabled by the service.".format(username)
            )
    except Exception as err:
        sut.add_test_result(
            CAT_NAME, test_name, operation, "FAIL", "Failed to enable user '{}' ({}).".format(username, err)
        )

    logger.log_use_case_test_footer(CAT_NAME, test_name)


def acc_test_credential_check(sut: SystemUnderTest, user_added: bool, username: str, password: str):
    """
    Performs the credential check test

    Args:
        sut: The system under test
        user_added: Indicates if the test user was added
        username: The username for testing
        password: The password for testing
    """

    test_name = TEST_CREDENTIAL_CHECK[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Skip the test if the test user was not added
    if not user_added:
        sut.add_test_result(
            CAT_NAME,
            test_name,
            "",
            "SKIP",
            "Failure of the '{}' test prevents performing this test.".format(TEST_ADD_USER[0]),
        )
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Log in with the new user
    operation = "Logging in as '{}' with the correct password".format(username)
    logger.logger.info(operation)
    test_obj = redfish.redfish_client(base_url=sut.rhost, username=username, password=password)
    try:
        test_obj.login(auth="session")
        test_list = redfish_utilities.get_users(test_obj)
        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
    except Exception as err:
        sut.add_test_result(
            CAT_NAME, test_name, operation, "FAIL", "Failed to login with user '{}' ({}).".format(username, err)
        )
    finally:
        try:
            test_obj.logout()
        except:
            pass

    # Log in with the new user, but with bad credentials
    operation = "Logging in as '{}', but with the incorrect password".format(username)
    logger.logger.info(operation)
    test_obj = redfish.redfish_client(base_url=sut.rhost, username=username, password=password + "ExtraStuff")
    try:
        test_obj.login(auth="session")
        test_list = redfish_utilities.get_users(test_obj)
        sut.add_test_result(
            CAT_NAME,
            test_name,
            operation,
            "FAIL",
            "Successful login with user '{}' when using invalid credentials.".format(username),
        )
    except:
        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
    finally:
        try:
            test_obj.logout()
        except:
            pass

    logger.log_use_case_test_footer(CAT_NAME, test_name)


def acc_test_change_role(sut: SystemUnderTest, user_added: bool, username: str):
    """
    Performs the change role test

    Args:
        sut: The system under test
        user_added: Indicates if the test user was added
        username: The username for testing
    """

    test_name = TEST_CHANGE_ROLE[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Skip the test if the test user was not added
    if not user_added:
        sut.add_test_result(
            CAT_NAME,
            test_name,
            "",
            "SKIP",
            "Failure of the '{}' test prevents performing this test.".format(TEST_ADD_USER[0]),
        )
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Change the role of the user
    test_roles = ["ReadOnly", "Operator", "Administrator"]
    for role in test_roles:
        operation = "Setting user '{}' to role '{}'".format(username, role)
        logger.logger.info(operation)
        try:
            redfish_utilities.modify_user(sut.session, username, new_role=role)
            if verify_user(sut.session, username, role=role):
                sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
            else:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAIL",
                    "Failed to find user '{}' with the role '{}' after successful PATCH.".format(username, role),
                )
        except Exception as err:
            http_bad_request = re.search("HTTP 400", str(err))
            not_writable = re.search("Base\\.1\\.\\d+.PropertyNotWritable", str(err))
            if http_bad_request and not_writable:
                sut.add_test_result(
                    CAT_NAME, test_name, operation, "SKIP", "Service does not support modifying 'RoleId'."
                )
            else:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAIL",
                    "Failed to set user '{}' to '{}' ({}).".format(username, role, err),
                )

    logger.log_use_case_test_footer(CAT_NAME, test_name)


def acc_test_delete_user(sut: SystemUnderTest, user_added: bool, username: str):
    """
    Performs the delete user test

    Args:
        sut: The system under test
        user_added: Indicates if the test user was added
        username: The username for testing
    """

    test_name = TEST_DELETE_USER[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Skip the test if the test user was not added
    if not user_added:
        sut.add_test_result(
            CAT_NAME,
            test_name,
            "",
            "SKIP",
            "Failure of the '{}' test prevents performing this test.".format(TEST_ADD_USER[0]),
        )
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Delete the user
    operation = "Deleting user '{}'".format(username)
    logger.logger.info(operation)
    try:
        redfish_utilities.delete_user(sut.session, username)
        if verify_user(sut.session, username):
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "User '{}' is still in the user list after successful DELETE.".format(username),
            )
        else:
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
    except Exception as err:
        sut.add_test_result(
            CAT_NAME, test_name, operation, "FAIL", "Failed to delete user '{}' ({}).".format(username, err)
        )

    logger.log_use_case_test_footer(CAT_NAME, test_name)
