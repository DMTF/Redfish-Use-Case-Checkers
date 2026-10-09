# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

import json
import time
from urllib.parse import urljoin

import redfish
import redfish_utilities

from redfish_use_case_checkers import logger


class _CapturedSession(object):
    """Proxy Redfish calls so reports can show the exchange behind a result."""

    _METHODS = ("get", "post", "patch", "put", "delete", "head")

    def __init__(self, client, sut):
        self._client = client
        self._sut = sut

    def __getattr__(self, name):
        attribute = getattr(self._client, name)
        if name not in self._METHODS or not callable(attribute):
            return attribute

        def call(*args, **kwargs):
            exchange = self._request(name, args, kwargs)
            self._sut._api_call_count += 1
            logger.log_api_call(exchange)
            started_at = time.monotonic()
            try:
                response = attribute(*args, **kwargs)
                exchange["Response"] = self._response_data(
                    response, (time.monotonic() - started_at) * 1000
                )
                return response
            except Exception as err:
                exchange["Error"] = str(err)
                raise
            finally:
                self._sut._last_exchange = exchange
                self._sut._exchange_history.append(exchange)

        return call

    def _request(self, method, args, kwargs):
        uri = kwargs.get("path") or kwargs.get("uri")
        if uri is None and args:
            uri = args[0]
        body = kwargs.get("body") or kwargs.get("payload")
        if body is None and method in ("post", "patch", "put") and len(args) > 1:
            body = args[1]
        headers = kwargs.get("headers") or {}
        request_headers = {str(key): self._safe_value(key, value) for key, value in headers.items()}
        request_headers.setdefault("Accept", "application/json")
        request_headers.setdefault("content-type", None)
        request_headers.setdefault("Authorization", "********")
        return {
            "method": method.upper(),
            "url": urljoin(self._sut.rhost.rstrip("/") + "/", str(uri or "")),
            "headers": request_headers,
            "data": self._json_value(body),
        }

    @staticmethod
    def _safe_value(key, value):
        key_name = str(key).lower().replace("_", "-")
        if (
            key_name in ("authorization", "x-auth-token", "password", "token", "access-token")
            or "token" in key_name
            or "secret" in key_name
        ):
            return "********"
        return value

    @classmethod
    def _json_value(cls, value):
        if isinstance(value, dict):
            return {
                str(key): cls._safe_value(key, cls._json_value(item))
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls._json_value(item) for item in value]
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            return str(value)

    @classmethod
    def _response_data(cls, response, response_time_ms=None):
        response_headers = getattr(response, "headers", None)
        if not response_headers and hasattr(response, "getheaders"):
            response_headers = response.getheaders()
        response_headers = response_headers or {}
        if hasattr(response_headers, "items"):
            response_headers = {
                str(key).lower(): cls._safe_value(key, value)
                for key, value in response_headers.items()
            }
        elif isinstance(response_headers, (list, tuple)):
            response_headers = {
                str(key).lower(): cls._safe_value(key, value)
                for key, value in response_headers
            }
        data = getattr(response, "dict", None)
        if data is None:
            data = getattr(response, "json", None)
            if callable(data):
                try:
                    data = data()
                except Exception:
                    data = None
        body = getattr(response, "text", getattr(response, "body", None))
        response_data = {
            "status": getattr(response, "status", getattr(response, "status_code", None)),
            "statusText": getattr(
                response, "statusText", getattr(response, "status_text", getattr(response, "reason", ""))
            ),
            "headers": response_headers,
            "data": cls._json_value(data),
        }
        if response_time_ms is not None:
            response_data["response_time_ms"] = response_time_ms
        response_data["response_size_bytes"] = cls._response_size_bytes(response_headers, data, body)
        for field in ("url", "elapsed", "http_version", "version", "encoding"):
            value = getattr(response, field, None)
            if value is not None:
                response_data[field] = cls._json_value(value)
        if body is not None and data is None:
            response_data["body"] = cls._json_value(body)
        return response_data

    @staticmethod
    def _response_size_bytes(headers, data, body):
        content_length = headers.get("content-length") if isinstance(headers, dict) else None
        try:
            return int(content_length)
        except (TypeError, ValueError):
            pass
        if body is not None:
            return len(str(body).encode("utf-8"))
        if data is not None:
            return len(json.dumps(data, default=str).encode("utf-8"))
        return 0


class SystemUnderTest(object):
    def __init__(self, rhost, username, password, relaxed):
        """
        Constructor for new system under test

        Args:
            rhost: The address of the Redfish service (with scheme)
            username: The username for authentication
            password: The password for authentication
            relaxed: Whether or not to apply relaxed testing criteria
        """
        self._rhost = rhost
        self._username = username
        self._relaxed = relaxed
        self._redfish_obj = redfish.redfish_client(
            base_url=rhost, username=username, password=password, timeout=15, max_retry=3
        )
        self._redfish_obj.login(auth="session")
        self._service_root = self._redfish_obj.root_resp.dict
        self._last_exchange = None
        self._exchange_history = []
        self._api_call_count = 0
        self._captured_session = _CapturedSession(self._redfish_obj, self)
        self._results = []
        self._pass_count = 0
        self._warn_count = 0
        self._fail_count = 0
        self._skip_count = 0

        # Find the manager to populate service info
        self._product = None
        self._product = self._service_root.get("Product", "N/A")
        self._fw_version = None
        self._model = None
        self._manufacturer = None
        if "Managers" in self._service_root:
            try:
                manager_ids = redfish_utilities.get_manager_ids(self._redfish_obj)
                if len(manager_ids) > 0:
                    manager = redfish_utilities.get_manager(self._redfish_obj, manager_ids[0])
                    self._fw_version = manager.dict.get("FirmwareVersion", "N/A")
                    self._model = manager.dict.get("Model", "N/A")
                    self._manufacturer = manager.dict.get("Manufacturer", "N/A")
            except:
                pass

    @property
    def rhost(self):
        """
        Accesses the address of the Redfish service

        Returns:
            The address of the Redfish service
        """
        return self._rhost

    @property
    def username(self):
        """
        Accesses the username for authentication

        Returns:
            The username for authentication
        """
        return self._username

    @property
    def firmware_version(self):
        """
        Accesses the firmware version of the service

        Returns:
            The firmware version of the service
        """
        return self._fw_version

    @property
    def model(self):
        """
        Accesses the model of the service

        Returns:
            The model of the service
        """
        return self._model

    @property
    def product(self):
        """
        Accesses the product of the service

        Returns:
            The product of the service
        """
        return self._product

    @property
    def manufacturer(self):
        """
        Accesses the manufacturer of the service

        Returns:
            The manufacturer of the service
        """
        return self._manufacturer

    @property
    def session(self):
        """
        Accesses the Redfish session

        Returns:
            The Redfish client object
        """
        return self._captured_session

    def new_session(self, username, password):
        """Creates a separately authenticated client using the shared capture proxy."""
        client = redfish.redfish_client(
            base_url=self._rhost,
            username=username,
            password=password,
            timeout=15,
            max_retry=3,
        )
        return _CapturedSession(client, self)

    @property
    def service_root(self):
        """
        Accesses the service root data

        Returns:
            The service root data as a dictionary
        """
        return self._service_root

    @property
    def pass_count(self):
        """
        Accesses the pass count

        Returns:
            The pass count
        """
        return self._pass_count

    @property
    def warn_count(self):
        """
        Accesses the warning count

        Returns:
            The warning count
        """
        return self._warn_count

    @property
    def fail_count(self):
        """
        Accesses the fail count

        Returns:
            The fail count
        """
        return self._fail_count

    @property
    def skip_count(self):
        """
        Accesses the skip count

        Returns:
            The skip count
        """
        return self._skip_count

    def logout(self):
        """
        Logs out of the Redfish service
        """
        self._redfish_obj.logout()
        print("Total API calls: {}".format(self._api_call_count), flush=True)

    def add_results_category(self, category, tests):
        """
        Adds a new category to the results

        Args:
            category: The name of the category
            tests: An array of test names and descriptions within the category
        """
        new_category = {"Category": category, "Tests": []}
        for test in tests:
            new_category["Tests"].append({"Name": test[0], "Description": test[1], "Details": test[2], "Results": []})
        self._results.append(new_category)

    def add_test_result(self, category_name, test_name, operation, result, msg=""):
        """
        Adds a new test result to the results

        Args:
            category_name: The name of the category
            test_name: The name of the test
            operation: The operation performed for the test
            result: The result of the test
            msg: A message for the test
        """
        for category in self._results:
            if category["Category"] == category_name:
                for test in category["Tests"]:
                    if test["Name"] == test_name:
                        exchanges = list(self._exchange_history)
                        self._exchange_history.clear()
                        test["Results"].append({
                            "Operation": operation,
                            "Result": result,
                            "Message": msg,
                            "Exchange": exchanges[-1] if exchanges else None,
                            "Exchanges": exchanges,
                        })
                        if result == "PASS":
                            self._pass_count += 1
                        elif result == "WARN" or (result == "FAILWARN" and self._relaxed is True):
                            logger.logger.warn("Warning occurred during the {} test...".format(test_name))
                            test["Results"][-1]["Result"] = "WARN"
                            logger.logger.warn(msg)
                            self._warn_count += 1
                        elif result == "FAIL" or result == "FAILWARN":
                            logger.logger.error("Failing the {} test...".format(test_name))
                            test["Results"][-1]["Result"] = "FAIL"
                            logger.logger.error(msg)
                            self._fail_count += 1
                        elif result == "SKIP":
                            logger.logger.info("Skipping the {} test...".format(test_name))
                            logger.logger.info(msg)
                            self._skip_count += 1
