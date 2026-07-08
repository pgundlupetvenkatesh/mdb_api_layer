"""
Test suite for the Networks API details endpoint.

This module contains integration tests for the NetworksAPI class, validating
both successful responses and error handling for ``GET /3/network/{network_id}``.
Tests are data-driven using external YAML test data files with pytest's
parametrize decorator.

Test data is loaded from 'test_data.yaml' which contains valid and invalid
test cases with expected values and defaults applied. Valid network IDs are
hardcoded, well-known networks (Netflix, HBO, BBC One, NBC) verified against
the live API.

Dependencies:
    - pytest: Test framework
    - pydantic: Response structure validation
    - NetworksAPI: API client under test
    - load_test_data: YAML test data loader

Usage:
    pytest tests/networks/test_details.py -v
"""

import allure
import pytest

from loguru import logger
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml", "get_network_details")
"""Module-level test data loaded once at import time for parametrization."""

@allure.epic("TMDB API")
@allure.feature("Networks")
class TestDetails(FieldAssertions):
    """
    Test class for Networks API get_network_details endpoint validation.

    Contains tests for the get_network_details endpoint covering both
    valid requests and error scenarios. Each test validates HTTP
    method, status codes, headers, response time, and body structure.
    """

    @allure.story("Get Network Details")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('network_details', TEST_DATA['get_network_details']['valid'])
    def test_get_network_details(self, networks_api, load_schema, network_details):
        """
        Test fetching network details with a valid network ID.

        Validates that the response returns the expected 200 status, correct
        HTTP metadata, the requested network ID echoed in the body, and a
        body that conforms to the strict NetworkDetails schema.

        :param networks_api: NetworksAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param network_details: Parametrized test data containing a valid
                                network_id, expected status_code, and reason.
        """
        logger.info(f"Testing get_network_details with network ID: {network_details['network_id']}")
        allure.dynamic.title(f"Get details for network ID: {network_details['network_id']}")

        with allure.step(f"Send GET request for network ID {network_details['network_id']}"):
            response = networks_api.get_network_details(network_details['network_id'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, network_details, 'network')

        with allure.step("Validate requested network ID is echoed in the response"):
            assert res_body['id'] == network_details['network_id']

        # NetworkDetails (strict) enforces the body structure, types, and field
        # semantics (strict types, logo path pattern, no extra fields).
        with allure.step("Validate response structure & schema (NetworkDetails)"):
            load_schema('network_details_schema').model_validate(res_body)

    @allure.story("Get Invalid Network Details")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('invalid_network_details', TEST_DATA['get_network_details']['invalid'])
    def test_get_network_details_invalid(self, networks_api, load_schema, invalid_network_details):
        """
        Test fetching network details with an invalid network ID.

        Validates that the API returns the expected error status code and
        message, with a body that conforms to the strict GenericResponse schema.

        :param networks_api: NetworksAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_network_details: Parametrized test data containing an
                                        invalid network_id, expected status_code,
                                        and expected_message.
        """
        logger.info(f"Testing get_network_details with invalid network ID: {invalid_network_details['network_id']}")
        allure.dynamic.title(f"Get details for invalid network ID: {invalid_network_details['network_id']}")

        with allure.step(f"Send GET request for network ID {invalid_network_details['network_id']}"):
            response = networks_api.get_network_details(invalid_network_details['network_id'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, invalid_network_details, 'network')

        with allure.step("Validate error message"):
            assert res_body['status_message'] == invalid_network_details['expected_message']
            assert res_body['success'] is False, "Request for an invalid network ID should report success=false"

        with allure.step("Validate response structure & schema (GenericResponse)"):
            load_schema('generic_schema').model_validate(res_body)