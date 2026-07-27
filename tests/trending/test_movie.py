"""
Test suite for the Trending API movie endpoint.

This module contains integration tests for the TrendingAPI class, validating
both successful responses and error handling for
``GET /3/trending/movie/{time_window}``. Tests are data-driven using external
YAML test data files with pytest's parametrize decorator.

Test data is loaded from 'test_data.yaml' which contains valid and invalid
test cases with expected values and defaults applied.

Dependencies:
    - pytest: Test framework
    - pydantic: Response structure validation
    - TrendingAPI: API client under test
    - load_test_data: YAML test data loader

Usage:
    pytest tests/trending/test_movie.py -v
"""

import allure
import pytest

from loguru import logger
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml", "trending_movies")
"""Module-level test data loaded once at import time for parametrization."""

@allure.epic("TMDB API")
@allure.feature("Trending")
class TestTrendingMovies(FieldAssertions):
    """
    Test class for Trending API movie endpoint validation.

    Contains tests for the get_trending_movies endpoint covering both valid
    requests across each supported time window and error scenarios. Each test
    validates HTTP method, status codes, headers, response time, and body
    structure.
    """

    @allure.story("Get Trending Movies")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('trending_case', TEST_DATA['trending_movies']['valid'])
    def test_get_trending_movies_valid(self, trending_api, load_schema, trending_case):
        """
        Test retrieving trending movies for each supported time window.

        Validates that a valid request returns the paginated results
        correctly, including response structure and content. The client
        defaults the page parameter to 1 when not supplied.

        :param trending_api: TrendingAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param trending_case: Parametrized test data containing a valid
                              time_window, optional query_param, and expected
                              status_code.
        """
        time_window = trending_case['time_window']
        allure.dynamic.title(f"Get trending movies for time window: {time_window}")
        logger.info(f"Testing get_trending_movies for time window: {time_window}")
        with allure.step(f"Send GET request for trending movies ({time_window})"):
            response = trending_api.get_trending_movies(time_window, query_params=trending_case.get('query_param'))
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, trending_case, f"trending/movie/{time_window}")

        with allure.step("Validate requested page is echoed in the response"):
            assert res_body['page'] == trending_case['exp_page']

        # TrendingMoviesResponse (strict) enforces pagination fields plus every
        # item's structure, types, and field semantics (non-empty results,
        # strict types, ISO/path/range rules).
        with allure.step("Validate response structure & schema (TrendingMoviesResponse)"):
            load_schema('trending_movies_schema').model_validate(res_body)

    @allure.story("Get Trending Movies with Invalid Query Params")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('invalid_test', TEST_DATA['trending_movies']['invalid'])
    def test_get_trending_movies_invalid(self, trending_api, load_schema, invalid_test):
        """
        Test retrieving trending movies with invalid parameters.

        Validates that appropriate error responses are returned when invalid
        query parameters are provided for the trending movies endpoint.

        :param trending_api: TrendingAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_test: Parametrized test data containing a valid
                             time_window, invalid query_param, expected
                             status_code, and expected_message.
        """
        time_window = invalid_test['time_window']
        allure.dynamic.title(f"Get trending movies with invalid query params: {invalid_test['query_param']}")
        logger.info(f"Testing get_trending_movies with invalid query params: {invalid_test['query_param']}")
        with allure.step(f"Send GET request for trending movies ({time_window})"):
            response = trending_api.get_trending_movies(time_window, query_params=invalid_test['query_param'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, invalid_test, f"trending/movie/{time_window}")

        with allure.step("Validate error message"):
            assert res_body['status_message'] == invalid_test['expected_message']

        with allure.step("Validate response structure & schema (GenericResponse)"):
            load_schema('generic_schema').model_validate(res_body)
