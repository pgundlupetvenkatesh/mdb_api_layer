"""
Test suite for the Discover API movie endpoint.

This module contains integration tests for the DiscoverAPI class, validating
both successful responses and error handling for ``GET /3/discover/movie``.
Tests are data-driven using external YAML test data files with pytest's
parametrize decorator.

Test data is loaded from 'test_data.yaml' which contains valid, empty-result
and invalid test cases with expected values and defaults applied.

Dependencies:
    - pytest: Test framework
    - pydantic: Response structure validation
    - DiscoverAPI: API client under test
    - load_test_data: YAML test data loader

Usage:
    pytest tests/discover/test_movie.py -v
"""

import allure
import pytest

from loguru import logger
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml", "discover_movies")
"""Module-level test data loaded once at import time for parametrization."""

@allure.epic("TMDB API")
@allure.feature("Discover")
class TestDiscoverMovies(FieldAssertions):
    """
    Test class for Discover API movie endpoint validation.

    Contains tests for the discover_movies endpoint covering discovery
    across a representative set of filter and sort parameters, filter
    combinations that match nothing, and error scenarios. Each test
    validates HTTP method, status codes, headers, response time, and
    body structure.
    """

    @allure.story("Discover Movies")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('discover_case', TEST_DATA['discover_movies']['valid'])
    def test_discover_movies_valid(self, discover_api, load_schema, discover_case):
        """
        Test discovering movies with each supported filter/sort parameter.

        Validates that a discovery request returns the paginated results
        correctly, including response structure and content. The client
        defaults the page parameter to 1 when not supplied.

        :param discover_api: DiscoverAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param discover_case: Parametrized test data containing valid query_param
                              and expected status_code.
        """
        allure.dynamic.title(f"Discover movies with query params: {discover_case['query_param']}")
        logger.info(f"Testing discover_movies with query params: {discover_case['query_param']}")
        with allure.step(f"Send GET request to discover movies"):
            response = discover_api.discover_movies(query_params=discover_case['query_param'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, discover_case, 'discover/movie')

        with allure.step("Validate requested page is echoed in the response"):
            assert res_body['page'] == discover_case['exp_page']

        # DiscoverMoviesResponse (strict) enforces pagination fields plus every
        # item's structure, types, and field semantics (non-empty results,
        # strict types, ISO/path/range rules).
        with allure.step("Validate response structure & schema (DiscoverMoviesResponse)"):
            load_schema('discover_movies_schema').model_validate(res_body)

    @allure.story("Discover Movies with No Matches")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('empty_case', TEST_DATA['discover_movies']['empty'])
    def test_discover_movies_empty_results(self, discover_api, empty_case):
        """
        Test discovering movies with filters that match nothing.

        TMDB returns 200 with an empty results page for these requests
        rather than an error, so the test asserts the empty pagination
        body directly (the discover schema requires at least one result,
        so it does not apply here).

        :param discover_api: DiscoverAPI client fixture from conftest.py.
        :param empty_case: Parametrized test data containing a query_param
                           that yields no matches and expected status_code.
        """
        allure.dynamic.title(f"Discover movies with no matches for query params: {empty_case['query_param']}")
        logger.info(f"Testing discover_movies with no expected matches for query params: {empty_case['query_param']}")
        with allure.step(f"Send GET request to discover movies"):
            response = discover_api.discover_movies(query_params=empty_case['query_param'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, empty_case, 'discover/movie')

        with allure.step("Validate empty paginated results"):
            assert res_body['results'] == []
            assert res_body['total_results'] == 0

    @allure.story("Discover Movies with Invalid Query Params")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('invalid_test', TEST_DATA['discover_movies']['invalid'])
    def test_discover_movies_invalid(self, discover_api, load_schema, invalid_test):
        """
        Test discovering movies with invalid parameters.

        Validates that appropriate error responses are returned when
        invalid query parameters are provided for the discover movie endpoint.

        :param discover_api: DiscoverAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_test: Parametrized test data containing invalid query_param,
                             expected status_code, and expected_message.
        """
        allure.dynamic.title(f"Discover movies with invalid query params: {invalid_test['query_param']}")
        logger.info(f"Testing discover_movies with invalid query params: {invalid_test['query_param']}")
        with allure.step(f"Send GET request to discover movies"):
            response = discover_api.discover_movies(query_params=invalid_test['query_param'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, invalid_test, 'discover/movie')

        with allure.step("Validate error message"):
            assert res_body['status_message'] == invalid_test['expected_message']

        with allure.step("Validate response structure & schema (GenericResponse)"):
            load_schema('generic_schema').model_validate(res_body)