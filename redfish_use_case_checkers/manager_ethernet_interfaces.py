# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

"""
Manager Ethernet Interfaces Use Cases

File : manager_ethernet_interfaces.py

Brief : This file contains the definitions and functionalities for testing
        use cases for manager Ethernet interfaces
"""

import logging
import redfish
import redfish_utilities

from redfish_use_case_checkers.system_under_test import SystemUnderTest
from redfish_use_case_checkers import logger

CAT_NAME = "Manager Ethernet Interfaces"
TEST_ETH_INT_COUNT = (
    "Ethernet Interface Count",
    "Verifies the Ethernet interface list for each manager is not empty",
    "Locates the EthernetInterfaceCollection resource for each manager and performs GET on all members.",
)
TEST_VLAN_CHECK = (
    "VLAN Check",
    "Verifies that an Ethernet interface represents VLAN information correctly",
    "Verifies the VLAN property is present along with its configuration properties.",
)
TEST_ADDRESSES_CHECK = (
    "Addresses Check",
    "Verifies that an Ethernet interface represents IP addresses correctly",
    "Verifies the properties related to IP addresses are present and contain valid values.",
)
TEST_LIST = [TEST_ETH_INT_COUNT, TEST_VLAN_CHECK, TEST_ADDRESSES_CHECK]


def use_cases(sut: SystemUnderTest):
    """
    Performs the use cases for manager Ethernet Interfaces

    Args:
        sut: The system under test
    """

    logger.log_use_case_category_header(CAT_NAME)

    # Set initial results
    sut.add_results_category(CAT_NAME, TEST_LIST)

    # Check that there is a manager collection
    if "Managers" not in sut.service_root:
        for test in TEST_LIST:
            sut.add_test_result(CAT_NAME, test[0], "", "SKIP", "Service does not contain a manager collection.")
        logger.log_use_case_category_footer(CAT_NAME)
        return

    # Go through the test cases
    test_interfaces = mgr_eth_int_test_interface_count(sut)
    mgr_eth_int_test_vlan_check(sut, test_interfaces)
    mgr_eth_int_test_addresses_check(sut, test_interfaces)

    logger.log_use_case_category_footer(CAT_NAME)


def invalid_address_check(address):
    """
    Determines if values contain invalid addresses

    Args:
        address: Dictionary, list, or string containing addresses

    Returns:
        The first invalid address found; None otherwise
    """

    invalid_addresses = ["", "0.0.0.0", "::"]

    if isinstance(address, dict):
        # Go through each property and check the value
        for prop in address:
            ret = invalid_address_check(address[prop])
            if ret is not None:
                return ret
    elif isinstance(address, list):
        # Go through each index and check the value
        for value in address:
            ret = invalid_address_check(value)
            if ret is not None:
                return ret
    elif isinstance(address, str):
        if address in invalid_addresses:
            return address

    return None


def mgr_eth_int_test_interface_count(sut: SystemUnderTest):
    """
    Performs the Ethernet interface count test

    Args:
        sut: The system under test

    Returns:
        An array of managers found
    """

    test_name = TEST_ETH_INT_COUNT[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)
    managers = {}

    # Get the list of managers
    operation = "Counting the members of the manager collection"
    logger.logger.info(operation)
    manager_ids = []
    try:
        manager_ids = redfish_utilities.get_manager_ids(sut.session)
        if len(manager_ids) == 0:
            sut.add_test_result(CAT_NAME, test_name, operation, "FAIL", "No managers were found.")
        else:
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
    except Exception as err:
        sut.add_test_result(CAT_NAME, test_name, operation, "FAIL", "Failed to get the manager list ({}).".format(err))

    # Go through each manager to find their Ethernet interfaces
    for manager_id in manager_ids:
        # Get the manager
        operation = "Getting manager '{}'".format(manager_id)
        logger.logger.info(operation)
        try:
            manager_resp = redfish_utilities.get_manager(sut.session, manager_id)
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
        except Exception as err:
            sut.add_test_result(
                CAT_NAME, test_name, operation, "FAIL", "Failed to get manager '{}' ({}).".format(manager_id, err)
            )
            continue

        # Get the list of Ethernet interfaces
        operation = "Counting the members of the Ethernet interface collection"
        logger.logger.info(operation)
        managers[manager_id] = []
        if "EthernetInterfaces" not in manager_resp.dict:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "SKIP",
                "Manager '{}' does not contain an Ethernet interface collection.".format(manager_id),
            )
            continue
        eth_int_ids = []
        try:
            eth_int_ids = redfish_utilities.get_manager_ethernet_interface_ids(sut.session, manager_id=manager_id)
            if len(eth_int_ids) == 0:
                sut.add_test_result(CAT_NAME, test_name, operation, "FAIL", "No Ethernet interfaces were found.")
            else:
                sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
        except Exception as err:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                operation,
                "FAIL",
                "Failed to get the Ethernet interface list for manager '{}' ({}).".format(manager_id, err),
            )

        # Get each Ethernet interface
        for interface_id in eth_int_ids:
            operation = "Getting Ethernet interface '{}' from manager '{}'".format(interface_id, manager_id)
            logger.logger.info(operation)
            try:
                eth_int_resp = redfish_utilities.get_manager_ethernet_interface(
                    sut.session, manager_id=manager_id, interface_id=interface_id
                )
                managers[manager_id].append(eth_int_resp.dict)
                sut.add_test_result(CAT_NAME, test_name, operation, "PASS")
            except Exception as err:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "FAIL",
                    "Failed to get Ethernet interface '{}' on manager '{}' ({}).".format(interface_id, manager_id, err),
                )

    logger.log_use_case_test_footer(CAT_NAME, test_name)
    return managers


def mgr_eth_int_test_vlan_check(sut: SystemUnderTest, eth_ints: dict):
    """
    Performs the VLAN check test

    Args:
        sut: The system under test
        eth_ints: The managers with Ethernet interfaces to test
    """

    test_name = TEST_VLAN_CHECK[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Skip the test if there are no managers
    if len(eth_ints) == 0:
        sut.add_test_result(CAT_NAME, test_name, "", "SKIP", "No managers were found.")
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Go through each manager
    for manager_id, eth_ints_list in eth_ints.items():
        # Skip the manager if there are no Ethernet interfaces
        if len(eth_ints_list) == 0:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                "",
                "SKIP",
                "Manager '{}' does not contain any Ethernet interfaces.".format(manager_id),
            )
            continue

        # Go through each Ethernet interface
        for eth_int in eth_ints_list:
            # Skip the Ethernet interface if it does not have a VLAN property
            operation = "Checking if Ethernet interface '{}' on manager '{}' has the 'VLAN' property".format(
                eth_int["Id"], manager_id
            )
            logger.logger.info(operation)
            if "VLAN" not in eth_int:
                sut.add_test_result(
                    CAT_NAME,
                    test_name,
                    operation,
                    "SKIP",
                    "Ethernet interface '{}' on manager '{}' does not have a VLAN.".format(eth_int["Id"], manager_id),
                )
                continue
            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

            # Check the properties inside the VLAN object
            property_check_list = ["VLANEnable", "VLANId", "VLANPriority", "Tagged"]
            req_property_check_list = ["VLANEnable", "VLANId"]
            for prop in property_check_list:
                operation = "Checking the '{}' property of Ethernet interface '{}' on manager '{}'".format(
                    prop, eth_int["Id"], manager_id
                )
                logger.logger.info(operation)
                if prop not in eth_int["VLAN"] and prop in req_property_check_list:
                    # Some properties are always expected to be present to ensure the object is useful
                    sut.add_test_result(
                        CAT_NAME, test_name, operation, "FAIL", "The '{}' property is not present.".format(prop)
                    )
                elif prop not in eth_int["VLAN"]:
                    sut.add_test_result(
                        CAT_NAME, test_name, operation, "SKIP", "The '{}' property is not present.".format(prop)
                    )
                else:
                    if eth_int["VLAN"][prop] is None:
                        # Null should only be used for error cases; the property should always have a valid value
                        sut.add_test_result(
                            CAT_NAME, test_name, operation, "WARN", "The '{}' property is null.".format(prop)
                        )
                    else:
                        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

    logger.log_use_case_test_footer(CAT_NAME, test_name)


def mgr_eth_int_test_addresses_check(sut: SystemUnderTest, eth_ints: dict):
    """
    Performs the addresses check test

    Args:
        sut: The system under test
        eth_ints: The managers with Ethernet interfaces to test
    """

    test_name = TEST_ADDRESSES_CHECK[0]
    logger.log_use_case_test_header(CAT_NAME, test_name)

    # Skip the test if there are no managers
    if len(eth_ints) == 0:
        sut.add_test_result(CAT_NAME, test_name, "", "SKIP", "No managers were found.")
        logger.log_use_case_test_footer(CAT_NAME, test_name)
        return

    # Go through each manager
    for manager_id, eth_ints_list in eth_ints.items():
        # Skip the manager if there are no Ethernet interfaces
        if len(eth_ints_list) == 0:
            sut.add_test_result(
                CAT_NAME,
                test_name,
                "",
                "SKIP",
                "Manager '{}' does not contain any Ethernet interfaces.".format(manager_id),
            )
            continue

        # Go through each Ethernet interface
        for eth_int in eth_ints_list:
            address_props = [
                "NameServers",
                "StaticNameServers",
                "IPv4Addresses",
                "IPv4StaticAddresses",
                "IPv6Addresses",
                "IPv6StaticAddresses",
                "IPv6DefaultGateway",
                "IPv6StaticDefaultGateways",
            ]
            non_null_props = ["NameServers", "IPv4Addresses", "IPv6Addresses"]
            ip_props = [
                "IPv4Addresses",
                "IPv4StaticAddresses",
                "IPv6Addresses",
                "IPv6StaticAddresses",
                "IPv6StaticDefaultGateways",
            ]
            for prop in address_props:
                # Check for the presence of the property
                operation = "Checking if Ethernet interface '{}' on manager '{}' contains the '{}' property".format(
                    eth_int["Id"], manager_id, prop
                )
                logger.logger.info(operation)
                if prop not in eth_int:
                    sut.add_test_result(
                        CAT_NAME, test_name, operation, "SKIP", "The '{}' property is not present.".format(prop)
                    )
                    continue
                sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

                # Check for invalid addresses
                operation = "Checking if Ethernet interface '{}' on manager '{}' does not contain invalid addresses in the '{}' property".format(
                    eth_int["Id"], manager_id, prop
                )
                logger.logger.info(operation)
                inv_address = invalid_address_check(eth_int[prop])
                if inv_address is not None:
                    sut.add_test_result(
                        CAT_NAME,
                        test_name,
                        operation,
                        "FAILWARN",
                        "The '{}' property contains the invalid address '{}'.".format(prop, inv_address),
                    )
                else:
                    sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

                # Check for null values
                if prop in non_null_props:
                    operation = "Checking if Ethernet interface '{}' on manager '{}' does not contain null values in the '{}' property".format(
                        eth_int["Id"], manager_id, prop
                    )
                    logger.logger.info(operation)
                    if None in eth_int[prop]:
                        sut.add_test_result(
                            CAT_NAME,
                            test_name,
                            operation,
                            "FAIL",
                            "The '{}' property contains one or more null values.".format(prop),
                        )
                    else:
                        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

                # Perform additional checks for IP address properties
                if prop in ip_props:
                    if "IPv4" in prop:
                        # Check that the gateway is only in the first address
                        operation = "Checking if Ethernet interface '{}' on manager '{}' only contains one gateway in the '{}' property".format(
                            eth_int["Id"], manager_id, prop
                        )
                        logger.logger.info(operation)
                        gateway_pass = True
                        for i, address in enumerate(eth_int[prop]):
                            if address is None:
                                # Static addresses can have null values
                                # Other tests in place for ensuring null is used correctly
                                continue
                            if "Gateway" in address and i != 0:
                                sut.add_test_result(
                                    CAT_NAME,
                                    test_name,
                                    operation,
                                    "FAIL",
                                    "The '{}' property contains a gateway address outside the first array member.".format(
                                        prop
                                    ),
                                )
                                gateway_pass = True
                                break
                            elif "Gateway" not in address and i == 0:
                                sut.add_test_result(
                                    CAT_NAME,
                                    test_name,
                                    operation,
                                    "FAIL",
                                    "The '{}' property does not have a gateway in the first array member.".format(prop),
                                )
                                gateway_pass = True
                                break
                        if gateway_pass:
                            sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

                    # Check for other expected properties
                    operation = "Checking if Ethernet interface '{}' on manager '{}' contains expected properties in the '{}' property".format(
                        eth_int["Id"], manager_id, prop
                    )
                    logger.logger.info(operation)
                    if "IPv4" in prop:
                        expected_properties = ["Address", "SubnetMask"]
                        if "Static" not in prop:
                            expected_properties.append("AddressOrigin")
                    else:
                        expected_properties = ["Address", "PrefixLength"]
                        if "Static" not in prop:
                            expected_properties.append("AddressOrigin")
                            expected_properties.append("AddressState")
                    exp_pass = True
                    for i, address in enumerate(eth_int[prop]):
                        if address is None:
                            # Static addresses can have null values
                            # Other tests in place for ensuring null is used correctly
                            continue
                        for exp_prop in expected_properties:
                            if exp_prop not in address:
                                sut.add_test_result(
                                    CAT_NAME,
                                    test_name,
                                    operation,
                                    "FAIL",
                                    "The '{}' property does not contain the '{}' property at index {}.".format(
                                        prop, exp_prop, i
                                    ),
                                )
                                exp_pass = False
                                break
                    if exp_pass:
                        sut.add_test_result(CAT_NAME, test_name, operation, "PASS")

    logger.log_use_case_test_footer(CAT_NAME, test_name)
