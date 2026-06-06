import allure
import pytest
from loguru import logger

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml", "delete_rating")
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

    @staticmethod
    def _assert_delete_metadata(response, case, url_contains):
        """
        Assert standard DELETE response metadata from a parametrized test case.

        Builds the expected-values dict from a test case (valid or invalid)
        and delegates to ``assert_http_response``, keeping the metadata key
        names in one place.

        :param response: APIResponse returned by the client.
        :param case: Parametrized test data dict (expects ``status_code``,
                     ``exp_max_elp_secs``, ``exp_del_req_method``,
                     ``exp_content_type``, ``reason``).
        :param url_contains: Substring expected in the response URL.
        """
        assert_http_response(response, {
            'exp_status_code': case['status_code'],
            'exp_max_elp_seconds': case['exp_max_elp_secs'],
            'exp_req_method': case['exp_del_req_method'],
            'exp_content_type': case['exp_content_type'],
            'exp_url_contains': str(url_contains),
            'exp_req_reason': case['reason']
        })

    @allure.story("Delete Movie Rating")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.order(2)
    @pytest.mark.parametrize('delete_valid_rating', TEST_DATA['delete_rating']['valid'])
    def test_delete_rating(self, movies_api, load_schema, delete_valid_rating):
        """
        Test deleting an existing movie rating with a valid session.

        Validates that deleting a previously rated movie returns the expected
        200 success response, correct HTTP metadata, and a body that conforms
        to the strict RatingResponse schema.

        :param movies_api: MoviesAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param delete_valid_rating: Parametrized test data containing the
                                     expected status_code, reason, and message.
        """
        movie_id = pick_random_rated_movie_id(Config.ACCOUNT_ID, Config.SESSION_ID)
        allure.dynamic.title(f"Delete movie rating for ID: {movie_id}")
        logger.info(f"Testing delete_rating for movie_id: {movie_id}")

        with allure.step(f"Send DELETE rating request for movie ID {movie_id}"):
            response = movies_api.delete_rating(movie_id, query_params=Config.SESSION_ID)
            res_json = response.data

        with allure.step("Validate HTTP response metadata"):
            self._assert_delete_metadata(response, delete_valid_rating, movie_id)

        with allure.step("Validate rating was deleted"):
            assert res_json['status_message'] == delete_valid_rating['expected_message']
            assert res_json['success'] is True, "Rating should be deleted successfully. Its false now"

        # RatingResponse (strict, extra="forbid") enforces the body structure/types.
        with allure.step("Validate response structure & schema (RatingResponse)"):
            load_schema('add_delete_rating_schema').model_validate(res_json)

    @allure.story("Delete Invalid Movie Rating")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('delete_invalid_rating', TEST_DATA['delete_rating']['invalid'])
    def test_delete_invalid_rating(self, movies_api, load_schema, delete_invalid_rating):
        """
        Test deleting a movie rating with an invalid movie ID (and, for one
        case, an invalid session ID).

        Validates that the API returns the expected error status code and
        message, with a body that conforms to the rating response schema.

        :param movies_api: MoviesAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param delete_invalid_rating: Parametrized test data containing invalid
                                      movie_id, optional session_id, expected
                                      status_code, and expected_message.
        """
        movie_id = delete_invalid_rating['movie_id']
        allure.dynamic.title(f"Delete movie rating for ID: {movie_id}")
        # Use session_id from test data if provided, otherwise use valid Config.SESSION_ID
        session_id = delete_invalid_rating.get('session_id', Config.SESSION_ID)
        logger.info(f"Testing {self._test_name} for movie_id: {movie_id} with session_id: {session_id}")

        with allure.step(f"Send DELETE rating request for invalid movie ID {movie_id}"):
            response = movies_api.delete_rating(movie_id, query_params=session_id)
            res_json = response.data

        with allure.step("Validate HTTP response metadata"):
            self._assert_delete_metadata(response, delete_invalid_rating, movie_id)

        with allure.step("Validate error message"):
            assert res_json['status_message'] == delete_invalid_rating['expected_message']
            assert res_json['success'] is False, "Delete on an invalid rating should report success=false"

        with allure.step("Validate response structure & schema (RatingResponse)"):
            load_schema('add_delete_rating_schema').model_validate(res_json)