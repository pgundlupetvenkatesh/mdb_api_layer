import allure
import pytest
from loguru import logger

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml")
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

    @allure.story("Update List Description")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('update_list', TEST_DATA['update_list']['valid'])
    def test_update_list_description(self, get_api_instance, load_schema, update_list):
        """
        Test updating a list with valid parameters.

        Validates that the list is updated correctly, including response structure and content.

        :param get_api_instance: Generic fixture instance.
        :param load_schema: Schema loader fixture from conftest.py
        :param update_list: Parametrized test data containing valid query_param,
                            expected status_code, and expected_message.
        """
        lists_api = get_api_instance('lists_api')
        allure.dynamic.title(f"Update Description for list ID {update_list['list_id']}")
        logger.debug(f"Testing update_list for list_id: {update_list['list_id']} with payload: {update_list['payload']}")

        with allure.step(f"Send PUT request to update list description"):
            response = lists_api.update_list(list_id=update_list['list_id'], payload=update_list['payload'])
            res_json = response.data

        logger.info(f"{self._test_name} - Actual maximum elapsed seconds: " + str(response.elapsed_seconds))
        with allure.step("Validate HTTP response metadata"):
            assert_http_response(response, {
                'exp_status_code': update_list['status_code'],
                'exp_max_elp_seconds': update_list['exp_max_elp_secs'],
                'exp_req_method': update_list['exp_put_req_method'],
                'exp_content_type': update_list['exp_content_type'],
                'exp_url_contains': f'list/{update_list["list_id"]}',
                'exp_req_reason': update_list['reason']
            })

        with allure.step("Validate response structure"):
            self.assert_bool_field(res_json, 'success')
            self.assert_int_field(res_json, 'status_code')
            self.assert_str_field(res_json, 'status_message')

        if 'success' in res_json:
            assert res_json['success'] is True, "Rating should be added successfully. Its false now"

            with allure.step("Validate against Pydantic schema"):
                load_schema('generic_schema').model_validate(res_json)

    @allure.story("Update Invalid List Description")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('update_list_invalid', TEST_DATA['update_list']['invalid'])
    def test_update_list_description_invalid(self, get_api_instance, load_schema, update_list_invalid):
        lists_api = get_api_instance('lists_api')
        allure.dynamic.title(f"Update Description for invalid list ID {update_list_invalid['list_id']}")
        logger.debug(
            f"Testing update_list for list_id: {update_list_invalid['list_id']} with payload: {update_list_invalid['payload']}")

        with allure.step(f"Send PUT request to update invalid list description"):
            response = lists_api.update_list(list_id=update_list_invalid['list_id'], payload=update_list_invalid['payload'])
            res_json = response.data

        logger.info(f"{self._test_name} - Actual maximum elapsed seconds: " + str(response.elapsed_seconds))
        with allure.step("Validate HTTP response metadata"):
            assert_http_response(response, {
                'exp_status_code': update_list_invalid['status_code'],
                'exp_max_elp_seconds': update_list_invalid['exp_max_elp_secs'],
                'exp_req_method': update_list_invalid['exp_put_req_method'],
                'exp_content_type': update_list_invalid['exp_content_type'],
                'exp_url_contains': f'list/{update_list_invalid["list_id"]}',
                'exp_req_reason': update_list_invalid['reason']
            })

        with allure.step("Validate response structure"):
            self.assert_bool_field(res_json, 'success')
            self.assert_int_field(res_json, 'status_code')
            self.assert_str_field(res_json, 'status_message')

        if 'success' in res_json:
            assert res_json['success'] is False, "Rating should not be added successfully. Its true now"

            with allure.step("Validate against Pydantic schema"):
                load_schema('generic_schema').model_validate(res_json)