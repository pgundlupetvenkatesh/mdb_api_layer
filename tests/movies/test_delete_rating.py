import allure
import pytest
from loguru import logger

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml")
"""Module-level test data loaded once at import time for parametrization."""

@allure.epic("TMDB API")
@allure.feature("Movies")
class TestDeleteRating(FieldAssertions):
    """
    Test class for Movies API delete_rating endpoint validation.

    Contains tests for the delete_rating endpoint covering both valid
    requests and error scenarios. Each test validates HTTP method,
    status codes, headers, response time, and body structure.
    """

    @allure.story("Delete Movie Rating")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.order(2)
    @pytest.mark.parametrize('delete_valid_rating', TEST_DATA['delete_rating']['valid'])
    def test_delete_rating(self, get_api_instance, load_schema, delete_valid_rating):
        """
        Test deleting a movie rating without authentication.

        Validates that attempting to delete a rating without proper
        authentication returns the expected error response.

        :param get_api_instance: Generic fixture instance.
        :param load_schema: Schema loader fixture from conftest.py.
        :param delete_valid_rating: Parametrized test data containing valid movie_id,
                                     expected status_code, and expected_message.
        """
        movie_id = pick_random_rated_movie_id(Config.ACCOUNT_ID, Config.SESSION_ID)
        allure.dynamic.title(f"Delete movie rating for ID: {movie_id}")
        logger.info(f"Testing delete_rating for movie_id: {movie_id}")
        movies_api = get_api_instance('movies_api')

        with allure.step(f"Send DELETE rating request for movie ID {movie_id}"):
            response = movies_api.delete_rating(movie_id, query_params=Config.SESSION_ID)
            res_json = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_http_response(response, {
                'exp_status_code': delete_valid_rating['status_code'],
                'exp_max_elp_seconds': delete_valid_rating['exp_max_elp_secs'],
                'exp_req_method': delete_valid_rating['exp_del_req_method'],
                'exp_content_type': delete_valid_rating['exp_content_type'],
                'exp_url_contains': str(movie_id),
                'exp_req_reason': delete_valid_rating['reason']
            })
            assert res_json['status_message'] == delete_valid_rating['expected_message']

        with allure.step("Validate response structure"):
            self.assert_str_field(res_json, 'status_message')
            self.assert_int_field(res_json, 'status_code')
            self.assert_int_field(res_json, 'success')

        if 'success' in res_json:
            assert res_json['success'] is True, "Rating should be deleted successfully. Its false now"

            with allure.step("Validate against Pydantic schema"):
                load_schema('add_delete_rating_schema').model_validate(res_json)

    @allure.story("Delete Invalid Movie Rating")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('delete_invalid_rating', TEST_DATA['delete_rating']['invalid'])
    def test_delete_invalid_rating(self, get_api_instance, load_schema, delete_invalid_rating):
        """
        Test deleting a movie rating with invalid movie ID in the first iteration and without session ID authentication.

        Validates that attempting to delete a rating without proper
        authentication returns the expected error response.

        :param get_api_instance: Generic fixture instance.
        :param load_schema: Schema loader fixture from conftest.py.
        :param delete_invalid_rating: Parametrized test data containing invalid movie_id,
                                      expected status_code, and expected_message.
        """
        movie_id = delete_invalid_rating['movie_id']
        allure.dynamic.title(f"Delete movie rating for ID: {movie_id}")
        # Use session_id from test data if provided, otherwise use valid Config.SESSION_ID
        session_id = delete_invalid_rating.get('session_id', Config.SESSION_ID)
        logger.info(f"Testing {self._test_name} for movie_id: {movie_id} with session_id: {session_id}")
        movies_api = get_api_instance('movies_api')

        with allure.step(f"Send DELETE rating request for invalid movie ID {movie_id}"):
            response = movies_api.delete_rating(movie_id, query_params=session_id)
            res_json = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_http_response(response, {
                'exp_status_code': delete_invalid_rating['status_code'],
                'exp_max_elp_seconds': delete_invalid_rating['exp_max_elp_secs'],
                'exp_req_method': delete_invalid_rating['exp_del_req_method'],
                'exp_content_type': delete_invalid_rating['exp_content_type'],
                'exp_url_contains': str(movie_id),
                'exp_req_reason': delete_invalid_rating['reason']
            })
            assert res_json['status_message'] == delete_invalid_rating['expected_message']

        with allure.step("Validate response structure"):
            self.assert_str_field(res_json, 'status_message')
            self.assert_int_field(res_json, 'status_code')
            self.assert_int_field(res_json, 'success')


        if 'success' in res_json:
            assert res_json['success'] is False, "Rating should be deleted successfully. Its false now"

            with allure.step("Validate against Pydantic schema"):
                load_schema('add_delete_rating_schema').model_validate(res_json)