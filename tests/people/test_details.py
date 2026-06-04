import allure
import pytest
from loguru import logger

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml")
"""Module-level test data loaded once at import time for parametrization."""

@allure.epic("TMDB API")
@allure.feature("People")
class TestDetails(FieldAssertions):
    """
    Test class for People API get_person_details endpoint validation.

    Contains tests for the get_person_details endpoint covering both
    valid requests and error scenarios. Each test validates HTTP
    method, status codes, headers, response time, and body structure.
    """

    @staticmethod
    def _assert_get_metadata(response, case, url_contains):
        """
        Assert standard GET response metadata from a parametrized test case.

        Builds the expected-values dict from a test case (valid or invalid)
        and delegates to ``assert_http_response``, keeping the metadata key
        names in one place.

        :param response: APIResponse returned by the client.
        :param case: Parametrized test data dict (expects ``status_code``,
                     ``exp_max_elp_secs``, ``exp_get_req_method``,
                     ``exp_content_type``, ``reason``).
        :param url_contains: Substring expected in the response URL.
        """
        assert_http_response(response, {
            'exp_status_code': case['status_code'],
            'exp_max_elp_seconds': case['exp_max_elp_secs'],
            'exp_req_method': case['exp_get_req_method'],
            'exp_content_type': case['exp_content_type'],
            'exp_url_contains': str(url_contains),
            'exp_req_reason': case['reason']
        })

    @allure.story("Get Person Details")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('person_details', TEST_DATA['get_person_details']['valid'])
    def test_get_person_details(self, people_api, load_schema, person_details):
        """
        Test fetching person details with a valid person ID.

        Validates that the response returns the expected 200 status, correct
        HTTP metadata, and a body that conforms to the strict PersonDetails
        schema.

        :param people_api: PeopleAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param person_details: Parametrized test data containing a valid
                               person_id, expected status_code, and reason.
        """
        logger.info(f"Random person ID picked: {person_details['person_id']}")
        allure.dynamic.title(f"Get details for person ID: {person_details['person_id']}")

        with allure.step(f"Send GET request for person ID {person_details['person_id']}"):
            response = people_api.get_person_details(person_details['person_id'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            self._assert_get_metadata(response, person_details, 'person')

        # PersonDetails (strict) enforces the body structure, types, and field
        # semantics (strict types, gender range, path pattern, nullability).
        with allure.step("Validate response structure & schema (PersonDetails)"):
            load_schema('person_details_schema').model_validate(res_body)

    @allure.story("Get Invalid Person Details")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('invalid_person_details', TEST_DATA['get_person_details']['invalid'])
    def test_get_person_details_invalid(self, people_api, load_schema, invalid_person_details):
        """
        Test fetching person details with an invalid person ID.

        Validates that the API returns the expected error status code and
        message, with a body that conforms to the strict GenericResponse schema.

        :param people_api: PeopleAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_person_details: Parametrized test data containing an
                                       invalid person_id, expected status_code,
                                       and expected_message.
        """
        allure.dynamic.title(f"Get details for invalid person ID: {invalid_person_details['person_id']}")

        with allure.step(f"Send GET request for person ID {invalid_person_details['person_id']}"):
            response = people_api.get_person_details(invalid_person_details['person_id'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            self._assert_get_metadata(response, invalid_person_details, 'person')

        with allure.step("Validate error message"):
            assert res_body['status_message'] == invalid_person_details['expected_message']
            assert res_body['success'] is False, "Request for an invalid person ID should report success=false"

        with allure.step("Validate response structure & schema (GenericResponse)"):
            load_schema('generic_schema').model_validate(res_body)