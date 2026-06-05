import allure
import pytest
from loguru import logger

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml", "update_list")
"""Module-level test data loaded once at import time for parametrization."""

@allure.epic("TMDB API")
@allure.feature("Lists")
class TestUpdate(FieldAssertions):
    """
    Test class for List Update API endpoint validation.

    Contains tests for the update_list endpoint covering both
    valid requests and error scenarios. Each test validates HTTP
    method, status codes, headers, response time, and body structure.
    """

    @staticmethod
    def _assert_put_metadata(response, case, url_contains):
        """
        Assert standard PUT response metadata from a parametrized test case.

        Builds the expected-values dict from a test case (valid or invalid)
        and delegates to ``assert_http_response``, keeping the metadata key
        names in one place.

        :param response: APIResponse returned by the client.
        :param case: Parametrized test data dict (expects ``status_code``,
                     ``exp_max_elp_secs``, ``exp_put_req_method``,
                     ``exp_content_type``, ``reason``).
        :param url_contains: Substring expected in the response URL.
        """
        assert_http_response(response, {
            'exp_status_code': case['status_code'],
            'exp_max_elp_seconds': case['exp_max_elp_secs'],
            'exp_req_method': case['exp_put_req_method'],
            'exp_content_type': case['exp_content_type'],
            'exp_url_contains': str(url_contains),
            'exp_req_reason': case['reason']
        })

    @allure.story("Update List Description")
    @allure.severity(allure.severity_level.CRITICAL)
    # TMDB's v4 list-write endpoint is intermittently very slow (occasional 19s+
    # responses and 30s ReadTimeouts), so retry transient latency/timeout flakes
    # before failing. Only the valid write is slow; invalid cases reject fast.
    @pytest.mark.flaky(reruns=2, reruns_delay=3)
    @pytest.mark.parametrize('update_list', TEST_DATA['update_list']['valid'])
    def test_update_list_description(self, lists_api, load_schema, update_list):
        """
        Test updating a list with valid parameters.

        Validates that the list is updated correctly, returning the expected
        201 success response, correct HTTP metadata, and a body that conforms
        to the strict GenericResponse schema.

        :param lists_api: ListsAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param update_list: Parametrized test data containing valid list_id,
                            payload, expected status_code, and expected_message.
        """
        allure.dynamic.title(f"Update Description for list ID {update_list['list_id']}")
        logger.debug(f"Testing update_list for list_id: {update_list['list_id']} with payload: {update_list['payload']}")

        with allure.step(f"Send PUT request to update list description"):
            response = lists_api.update_list(list_id=update_list['list_id'], payload=update_list['payload'])
            res_json = response.data

        logger.info(f"{self._test_name} - Actual maximum elapsed seconds: " + str(response.elapsed_seconds))
        with allure.step("Validate HTTP response metadata"):
            self._assert_put_metadata(response, update_list, f'list/{update_list["list_id"]}')

        with allure.step("Validate list was updated"):
            assert res_json['status_message'] == update_list['expected_message']
            assert res_json['success'] is True, "List should be updated successfully. Its false now"

        # GenericResponse (strict, extra="forbid") enforces the body structure/types.
        with allure.step("Validate response structure & schema (GenericResponse)"):
            load_schema('generic_schema').model_validate(res_json)

    @allure.story("Update Invalid List Description")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('update_list_invalid', TEST_DATA['update_list']['invalid'])
    def test_update_list_description_invalid(self, lists_api, load_schema, update_list_invalid):
        """
        Test updating a list with an invalid list ID.

        Validates that the API returns the expected error status code and
        message, with a body that conforms to the strict GenericResponse schema.

        :param lists_api: ListsAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param update_list_invalid: Parametrized test data containing invalid
                                    list_id, payload, expected status_code, and
                                    expected_message.
        """
        allure.dynamic.title(f"Update Description for invalid list ID {update_list_invalid['list_id']}")
        logger.debug(
            f"Testing update_list for list_id: {update_list_invalid['list_id']} with payload: {update_list_invalid['payload']}")

        with allure.step(f"Send PUT request to update invalid list description"):
            response = lists_api.update_list(list_id=update_list_invalid['list_id'], payload=update_list_invalid['payload'])
            res_json = response.data

        logger.info(f"{self._test_name} - Actual maximum elapsed seconds: " + str(response.elapsed_seconds))
        with allure.step("Validate HTTP response metadata"):
            self._assert_put_metadata(response, update_list_invalid, f'list/{update_list_invalid["list_id"]}')

        with allure.step("Validate error message"):
            assert res_json['status_message'] == update_list_invalid['expected_message']
            assert res_json['success'] is False, "Update on an invalid list should report success=false"

        with allure.step("Validate response structure & schema (GenericResponse)"):
            load_schema('generic_schema').model_validate(res_json)