# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

"""
Query Parameters Use Cases

File : query_parameters.py

Brief : This file contains the definitions and functionalities for testing
        use cases for query parameters
"""

import logging
import re
import redfish
import redfish_utilities

from redfish_use_case_checkers.system_under_test import SystemUnderTest
from redfish_use_case_checkers import logger

CAT_NAME = "Query Parameters"
TEST_FILTER_QUERY = (
    "Filter Query",
    "Verifies the service correctly performs $filter queries",
    "Locates the RoleCollection resource for the service.  Performs $filter queries to look for matching values of the Id property.",
)
TEST_SELECT_QUERY = (
    "Select Query",
    "Verifies the service correctly performs $select queries",
    "Locates a Role resource from the service.  Performs $select queries and compares the response to ensure only expected properties are provided.",
)
TEST_EXPAND_QUERY = (
    "Expand Query",
    "Verifies the service correctly performs $expand queries",
    "Performs various $expand queries on the ServiceRoot resource and verifies that expansion is performed correctly.",
)
TEST_ONLY_QUERY = (
    "Only Query",
    "Verifies the service correctly performs only queries",
    "Performs various only queries on resources subordinate to the ServiceRoot resource.  Verifies that the responses are correct.",
)
TEST_LIST = [
    TEST_FILTER_QUERY,
    TEST_SELECT_QUERY,
    TEST_EXPAND_QUERY,
    TEST_ONLY_QUERY,
]


def use_cases(sut: SystemUnderTest):
    """
    Performs the use cases for query parameters

    Args:
        sut: The system under test
    """

    logger.log_use_case_category_header(CAT_NAME)

    # Set initial results
    sut.add_results_category(CAT_NAME, TEST_LIST)

    # Check that there is an account service
    if "ProtocolFeaturesSupported" not in sut.service_root:
        for test in TEST_LIST:
            sut.add_test_result(
                CAT_NAME, test[0], "", "SKIP", "Service does not support the ProtocolFeaturesSupported property."
            )
        logger.log_use_case_category_footer(CAT_NAME)
        return

    # Go through the test cases
    query_test_filter(sut)
    query_test_select(sut)
    query_test_expand(sut)
    query_test_only(sut)
    logger.log_use_case_category_footer(CAT_NAME)


def get_role_collection(sut: SystemUnderTest):
    """
    Gets the role collection for testing queries

    Args:
        sut: The system under test

    Returns:
        The URI of the role collection
        The number of roles in the role collection
        A dictionary of the first role
        A dictionary of the last role
    """

    operation = "Locating the role collection"
    logger.logger.info(operation)
    try:
        # Check for the presence of the account service
        if "AccountService" not in sut.service_root:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "Account service not found.",
            )
            return None, None, None, None
        account_service = sut.session.get(sut.service_root["AccountService"]["@odata.id"])
        redfish_utilities.verify_response(account_service)

        # Check for the presence of the role collection
        if "Roles" not in account_service.dict:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "Role collection not found.",
            )
            return None, None, None, None
        role_collection_uri = account_service.dict["Roles"]["@odata.id"]
        role_collection = sut.session.get(role_collection_uri)
        redfish_utilities.verify_response(role_collection)
        role_count = len(role_collection.dict["Members"])
        if role_count == 0:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "Role collection is empty.",
            )
            return None, None, None, None

        # Get the first and last roles to be used for building $filter parameters
        role_first = sut.session.get(role_collection.dict["Members"][0]["@odata.id"])
        redfish_utilities.verify_response(role_first)
        role_first_uri = role_first.dict["@odata.id"]
        role_last = sut.session.get(role_collection.dict["Members"][-1]["@odata.id"])
        redfish_utilities.verify_response(role_last)
    except Exception as err:
        sut.add_test_result(
            CAT_NAME, test_name, operation, "FAIL", "Failed to get the role collection ({}).".format(err)
        )
        return None, None, None, None

    return role_collection_uri, role_count, role_first.dict, role_last.dict


def query_test_filter(sut: SystemUnderTest):
    """
    Performs the filter query test

    Args:
        sut: The system under test
    """

    test_name = TEST_FILTER_QUERY[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Check if $filter is supported
    if not sut.service_root["ProtocolFeaturesSupported"].get("FilterQuery", False):
        sut.add_test_result(
            CAT_NAME,
            test_name,
            "",
            "SKIP",
            "Service does not support $filter.",
        )
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Locate the role collection for testing
    role_collection_uri, role_count, role_first, role_last = get_role_collection(sut)
    if role_collection_uri is None:
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Perform various $filter requests on the collection and check the members returned
    first_and_last = 2
    if role_first["@odata.id"] == role_last["@odata.id"]:
        first_and_last = 1
    filter_checks = [
        {
            "Description": "Match exactly one",
            "Query": {"$filter": "Id eq '" + role_first["Id"] + "'"},
            "ExpectedLength": 1,
        },
        {
            "Description": "Match exactly everything except one",
            "Query": {"$filter": "not (Id eq '" + role_first["Id"] + "')"},
            "ExpectedLength": role_count - 1,
        },
        {
            "Description": "Match first or last",
            "Query": {"$filter": "Id eq '" + role_first["Id"] + "'" + " or Id eq '" + role_last["Id"] + "'"},
            "ExpectedLength": first_and_last,
        },
    ]
    for check in filter_checks:
        operation = check["Description"]
        logger.logger.info(operation)
        try:
            query_str = "$filter=" + check["Query"]["$filter"]
            logger.logger.debug("Performing {} on {}".format(query_str, role_collection_uri))
            filter_list = sut.session.get(role_collection_uri, args=check["Query"])
            redfish_utilities.verify_response(filter_list)
            filter_count = len(filter_list.dict["Members"])
            if filter_count != check["ExpectedLength"]:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAIL",
                    "Query ({}) expected to return {} member(s); received {}.".format(
                        query_str, check["ExpectedLength"], filter_count
                    ),
                )
            else:
                sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
        except Exception as err:
            sut.add_test_result(
                CAT_NAME, test_name, operation, "FAIL", "Failed to perform the $filter query ({}).".format(err)
            )

    # Perform a $filter query on an individual role and ensure the request is rejected
    operation = "Invalid request on a non-collection resource"
    logger.logger.info(operation)
    try:
        query = {"$filter": "Id eq '" + role_first["Id"] + "'"}
        query_str = "$filter=" + query["$filter"]
        logger.logger.debug("Performing {} on {}".format(query_str, role_first["@odata.id"]))
        filter_response = sut.session.get(role_first["@odata.id"], args=query)
        try:
            redfish_utilities.verify_response(filter_response)
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "Query ({}) expected to result in an error, but succeeded.".format(query_str),
            )
        except:
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
    except Exception as err:
        sut.add_test_result(
            CAT_NAME, test_name, operation, "FAIL", "Failed to perform the $filter query ({}).".format(err)
        )

    logger.log_use_case_test_footer(CAT_NAME, test_name)
    return


def query_test_select(sut: SystemUnderTest):
    """
    Performs the select query test

    Args:
        sut: The system under test
    """

    test_name = TEST_SELECT_QUERY[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Check if $select is supported
    if not sut.service_root["ProtocolFeaturesSupported"].get("SelectQuery", False):
        sut.add_test_result(
            CAT_NAME,
            test_name,
            "",
            "SKIP",
            "Service does not support $select.",
        )
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Locate the role collection for testing
    role_collection_uri, role_count, role_first, role_last = get_role_collection(sut)
    if role_collection_uri is None:
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Perform a $select query
    operation = "Request the 'Name' and 'AssignedPrivileges' properties."
    logger.logger.info(operation)
    try:
        query = {"$select": "Name,AssignedPrivileges"}
        query_str = "$select=" + query["$select"]
        logger.logger.debug("Performing {} on {}".format(query_str, role_first["@odata.id"]))
        select_response = sut.session.get(role_first["@odata.id"], args=query)
        redfish_utilities.verify_response(select_response)
        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
    except Exception as err:
        sut.add_test_result(
            CAT_NAME, test_name, operation, "FAIL", "Failed to perform the $select query ({}).".format(err)
        )
        return

    # Check the response for the expected properties
    required_properties = ["@odata.id", "@odata.type", "Name", "AssignedPrivileges"]
    conditional_properties = ["@odata.context", "@odata.etag"]
    select_dict = select_response.dict

    # Check for mandatory properties
    # These are either mandatory per the spec or per the $select request
    for required in required_properties:
        operation = "Checking for '{}' property in the response.".format(required)
        logger.logger.info(operation)

        # Check that the select response contains the required property and that it matches
        if required not in select_dict:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "Query ({}) response expected to contain property '{}'.".format(query_str, required),
            )
        elif select_dict[required] != role_first.get(required):
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "Query ({}) response contains different property value for '{}'.".format(query_str, required),
            )
        else:
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
        if required in select_dict:
            select_dict.pop(required)

    # Check for conditional properties
    # These are mandatory per the spec if the resource supports them
    for conditional in conditional_properties:
        operation = "Checking for '{}' property in the response.".format(conditional)
        logger.logger.info(operation)

        # Check that the select response contains the conditional property if it's supported and that it matches
        if conditional not in select_dict and conditional in role_first:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "Query ({}) response expected to contain property {}.".format(query_str, conditional),
            )
        elif (
            conditional in select_dict
            and conditional in role_first
            and select_dict[conditional] != role_first[conditional]
        ):
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "Query ({}) response contains different property value for '{}'.".format(query_str, conditional),
            )
        else:
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
        if conditional in select_dict:
            select_dict.pop(conditional)

    # Check for extra properties
    operation = "Checking for extra properties in the response."
    logger.logger.info(operation)
    extra_list = []
    for extra in select_dict:
        extra_list.append(extra)
    if len(extra_list) != 0:
        sut.add_test_result(
            CAT_NAME,
            test_name,
            operation,
            "FAIL",
            "Query ({}) response contains extra properties: {}.".format(query_str, ",".join(extra_list)),
        )
    else:
        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

    logger.log_use_case_test_footer(CAT_NAME, test_name)
    return


def verify_expand(query, name, value, is_expanded):
    """
    Verifies an object is expanded properly

    Args:
        query: The query string used
        name: The name of the property
        value: The value of the property
        is_expanded: If expansion is expected
    """

    query_str = "$expand=" + query["$expand"]
    if "@odata.id" in value:
        if len(value) == 1:
            if is_expanded:
                raise ValueError("Resource '{}' was expected to be expanded".format(name))
        else:
            if not is_expanded:
                raise ValueError("Resource '{}' was not expected to be expanded".format(name))


def query_test_expand(sut: SystemUnderTest):
    """
    Performs the expand query test

    Args:
        sut: The system under test
    """

    test_name = TEST_EXPAND_QUERY[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Check if $expand is supported
    if "ExpandQuery" not in sut.service_root["ProtocolFeaturesSupported"]:
        sut.add_test_result(
            CAT_NAME,
            test_name,
            "",
            "SKIP",
            "Service does not support $expand.",
        )
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    expand_checks = [
        {
            "Term": "ExpandAll",
            "Query": {"$expand": "*"},
            "Sub": True,
            "Links": True,
            "Levels": False,
            "Description": "Performing expand all with no levels specified.",
        },
        {
            "Term": "NoLinks",
            "Query": {"$expand": "."},
            "Sub": True,
            "Links": False,
            "Levels": False,
            "Description": "Performing expand subordinate with no levels specified.",
        },
        {
            "Term": "Links",
            "Query": {"$expand": "~"},
            "Sub": False,
            "Links": True,
            "Levels": False,
            "Description": "Performing expand links with no levels specified.",
        },
        {
            "Term": "ExpandAll",
            "Query": {"$expand": "*($levels=1)"},
            "Sub": True,
            "Links": True,
            "Levels": True,
            "Description": "Performing expand all with 1 level specified.",
        },
        {
            "Term": "NoLinks",
            "Query": {"$expand": ".($levels=1)"},
            "Sub": True,
            "Links": False,
            "Levels": True,
            "Description": "Performing expand subordinate with 1 level specified.",
        },
        {
            "Term": "Links",
            "Query": {"$expand": "~($levels=1)"},
            "Sub": False,
            "Links": True,
            "Levels": True,
            "Description": "Performing expand links with 1 level specified.",
        },
    ]

    # Go through each of the different expand types
    check_uri = "/redfish/v1/"
    for check in expand_checks:
        operation = check["Description"]
        logger.logger.info(operation)

        # Check if the type of expansion is supported
        if not sut.service_root["ProtocolFeaturesSupported"]["ExpandQuery"].get(check["Term"], False):
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "Service does not support '{}'.".format(check["Term"]),
            )
            continue
        if not sut.service_root["ProtocolFeaturesSupported"]["ExpandQuery"].get("Levels", False) and check["Levels"]:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "Service does not support specifying expansion levels.",
            )
            continue

        # Perform the query on service root
        try:
            logger.logger.debug("Performing $expand={} on {}".format(check["Query"]["$expand"], check_uri))
            expand_response = sut.session.get(check_uri, args=check["Query"])
            redfish_utilities.verify_response(expand_response)
        except Exception as err:
            sut.add_test_result(
                CAT_NAME, test_name, operation, "FAIL", "Failed to perform the $expand query ({}).".format(err)
            )
            continue

        # Check the response to ensure things are expanded properly
        try:
            for property in expand_response.dict:
                if property == "Links":
                    # Links object; scan it for expansion
                    for link_property in expand_response.dict[property]:
                        if isinstance(expand_response.dict[property][link_property], dict):
                            verify_expand(
                                check["Query"],
                                link_property,
                                expand_response.dict[property][link_property],
                                check["Links"],
                            )
                        elif isinstance(expand_response.dict[property][link_property], list):
                            for link_item in expand_response.dict[property][link_property]:
                                verify_expand(check["Query"], link_property, link_item, check["Links"])
                elif isinstance(expand_response.dict[property], dict):
                    # Non-Links object; check if this is a reference object and if it was expanded properly
                    verify_expand(check["Query"], property, expand_response.dict[property], check["Sub"])
        except Exception as err:
            sut.add_test_result(
                CAT_NAME, test_name, operation, "FAIL", "$expand contains unexpected results: {}.".format(err)
            )
            continue

        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

    logger.log_use_case_test_footer(CAT_NAME, test_name)
    return


def query_test_only(sut: SystemUnderTest):
    """
    Performs the only query test

    Args:
        sut: The system under test
    """

    test_name = TEST_ONLY_QUERY[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Check if only is supported
    if not sut.service_root["ProtocolFeaturesSupported"].get("OnlyMemberQuery", False):
        sut.add_test_result(
            CAT_NAME,
            test_name,
            "",
            "SKIP",
            "Service does not support only.",
        )
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # List of service root properties to inspect; True indicates if the reference is to a collection
    only_checks = {"AccountService": False, "SessionService": False, "Chassis": True, "Systems": True, "Managers": True}

    # Go through each of the service root properties and test the only query
    query = {"only": None}
    query_str = "only"
    for check in only_checks:
        operation = "Performing only on {}.".format(check)
        logger.logger.info(operation)

        if check not in sut.service_root:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "Service does not contain '{}'.".format(check),
            )
            continue

        try:
            check_uri = sut.service_root[check]["@odata.id"]
            logger.logger.debug("Performing {} on {}".format(query_str, check_uri))

            if only_checks[check]:
                # Testing a collection
                only_response = sut.session.get(check_uri, args=query)
                redfish_utilities.verify_response(only_response)
                resource_response = sut.session.get(check_uri)
                redfish_utilities.verify_response(resource_response)
                if len(resource_response.dict["Members"]) == 1:
                    # Collection has exactly one member; query response is supposed to be the one member
                    if only_response.dict["@odata.id"] == resource_response.dict["Members"][0]["@odata.id"]:
                        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
                    else:
                        sut.add_test_result(
                            CAT_NAME,
                            test_name,
                            operation,
                            "FAIL",
                            "Query ({}) response for {} expected the only collection member.".format(
                                query_str, check_uri
                            ),
                        )
                else:
                    # Collection does not have exactly one member; query response is supposed to be the collection itself
                    if (
                        only_response.dict["@odata.id"] != resource_response.dict["@odata.id"]
                        or "Members" not in only_response.dict
                    ):
                        sut.add_test_result(
                            CAT_NAME,
                            test_name,
                            operation,
                            "FAIL",
                            "Query ({}) response for {} expected the collection itself.".format(query_str, check_uri),
                        )
                    else:
                        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
            else:
                # Testing a singular resource; this is supposed to produce an error for the client
                only_response = sut.session.get(check_uri, args=query)
                try:
                    redfish_utilities.verify_response(only_response)
                    sut.add_test_result(
                        CAT_NAME,
                        test_name,
                        operation,
                        "FAIL",
                        "Query ({}) expected to result in an error for {}, but succeeded.".format(query_str, check_uri),
                    )
                except:
                    sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
        except Exception as err:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "Failed to perform the only query or access the resource under test ({}).".format(err),
            )

    logger.log_use_case_test_footer(CAT_NAME, test_name)
    return
