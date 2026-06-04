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
class TestAddRating(FieldAssertions):
    """
    Test class for Movies API add_rating endpoint validation.

    Contains tests for the add_rating endpoint covering both valid
    requests and error scenarios. Each test validates HTTP method,
    status codes, headers, response time, and body structure.
    """

    @staticmethod
    def _assert_post_metadata(response, case, url_contains):
        """
        Assert standard POST response metadata from a parametrized test case.

        Builds the expected-values dict from a test case (valid or invalid)
        and delegates to ``assert_http_response``, keeping the metadata key
        names in one place.

        :param response: APIResponse returned by the client.
        :param case: Parametrized test data dict (expects ``status_code``,
                     ``exp_max_elp_secs``, ``exp_post_req_method``,
                     ``exp_content_type``, ``reason``).
        :param url_contains: Substring expected in the response URL.
        """
        assert_http_response(response, {
            'exp_status_code': case['status_code'],
            'exp_max_elp_seconds': case['exp_max_elp_secs'],
            'exp_req_method': case['exp_post_req_method'],
            'exp_content_type': case['exp_content_type'],
            'exp_url_contains': str(url_contains),
            'exp_req_reason': case['reason']
        })

    @allure.story("Add Movie Rating")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.order(1)
    @pytest.mark.parametrize('add_valid_rating', TEST_DATA['add_rating']['valid'])
    def test_add_rating(self, movies_api, load_schema, add_valid_rating):
        """
        Test adding a movie rating with a valid session.

        Validates that a valid rating submission returns the expected 201
        success response, correct HTTP metadata, and a body that conforms
        to the strict RatingResponse schema.

        :param movies_api: MoviesAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param add_valid_rating: Parametrized test data containing the rating
                                 payload, expected status_code, and reason.
        """
        movie_id = pick_random_movie_id()
        rating = add_valid_rating['rating_payload']['value']
        allure.dynamic.title(f"Add rating {rating} for movie ID: {movie_id}")
        logger.info(f"Testing add_rating for movie_id: {movie_id} with rating: {rating}")

        with allure.step(f"Send Add(POST) rating request for movie ID {movie_id}"):
            response = movies_api.add_rating(movie_id, rating, query_params=Config.SESSION_ID)
            res_json = response.data

        with allure.step("Validate HTTP response metadata"):
            self._assert_post_metadata(response, add_valid_rating, movie_id)

        with allure.step("Validate rating was added"):
            assert res_json['success'] is True, "Rating should be added successfully. Its false now"

        # RatingResponse (strict, extra="forbid") enforces the body structure/types.
        with allure.step("Validate response structure & schema (RatingResponse)"):
            load_schema('add_delete_rating_schema').model_validate(res_json)

    @allure.story("Add Movie Rating - Invalid Value")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('add_invalid_rating', TEST_DATA['add_rating']['invalid'])
    def test_add_rating_unauthenticated(self, movies_api, load_schema, add_invalid_rating):
        """
        Test adding a movie rating with an invalid rating value.

        Validates that submitting an out-of-range rating value returns the
        expected 400 Bad Request with one of the accepted validation messages.

        :param movies_api: MoviesAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param add_invalid_rating: Parametrized test data containing movie_id, an
                                   invalid rating payload, expected status_code,
                                   and the set of acceptable validation messages.
        """
        movie_id = add_invalid_rating['movie_id']
        rating = add_invalid_rating['rating_payload']['value']
        allure.dynamic.title(f"Add rating {rating} for movie ID: {movie_id}")
        logger.info(f"Testing add_rating for movie_id: {movie_id} with invalid rating: {rating}")

        with allure.step(f"Send Add(POST) rating request for movie ID {movie_id}"):
            response = movies_api.add_rating(movie_id, rating, query_params=Config.SESSION_ID)
            res_json = response.data

        with allure.step("Validate HTTP response metadata"):
            self._assert_post_metadata(response, add_invalid_rating, movie_id)

        with allure.step("Validate error message"):
            assert res_json['status_message'] in add_invalid_rating['expected_message'], \
                f"Unexpected message: '{res_json['status_message']}' not in {add_invalid_rating['expected_message']}"

        with allure.step("Validate response structure & schema (GenericResponse)"):
            load_schema('generic_schema').model_validate(res_json)