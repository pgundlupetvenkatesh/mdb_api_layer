"""
Test suite for the Search API movie endpoint.

This module contains integration tests for the SearchAPI class, validating
both successful responses and error handling for ``GET /3/search/movie``.
Tests are data-driven using external YAML test data files with pytest's
parametrize decorator.

Test data is loaded from 'test_data.yaml' which contains valid, empty-result
and invalid test cases with expected values and defaults applied.

Dependencies:
    - pytest: Test framework
    - pydantic: Response structure validation
    - SearchAPI: API client under test
    - load_test_data: YAML test data loader

Usage:
    pytest tests/search/test_movie.py -v
"""

import allure
import pytest

from loguru import logger
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml", "search_movies")
"""Module-level test data loaded once at import time for parametrization."""

@allure.epic("TMDB API")
@allure.feature("Search")
class TestSearchMovies(FieldAssertions):
    """
    Test class for Search API movie endpoint validation.

    Contains tests for the search_movies endpoint covering matched searches
    across every supported query parameter, valid searches with no matches,
    and error scenarios. Each test validates HTTP method, status codes,
    headers, response time, and body structure.
    """

    @allure.story("Search Movies")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('search_case', TEST_DATA['search_movies']['valid'])
    def test_search_movies_valid(self, search_api, load_schema, search_case):
        """
        Test searching movies with each supported query parameter.

        Validates that a matched search returns the paginated results
        correctly, including response structure and content. The client
        defaults the page parameter to 1 when not supplied.

        :param search_api: SearchAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param search_case: Parametrized test data containing valid query_param
                            and expected status_code.
        """
        allure.dynamic.title(f"Search movies with query params: {search_case['query_param']}")
        logger.info(f"Testing search_movies with query params: {search_case['query_param']}")
        with allure.step(f"Send GET request to search movies"):
            response = search_api.search_movies(query_params=search_case['query_param'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, search_case, 'search/movie')

        # SearchMoviesResponse (strict) enforces pagination fields plus every
        # item's structure, types, and field semantics (non-empty results,
        # strict types, ISO/path/range rules).
        with allure.step("Validate response structure & schema (SearchMoviesResponse)"):
            load_schema('search_movies_schema').model_validate(res_body)

    @allure.story("Search Movies with No Matches")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('empty_case', TEST_DATA['search_movies']['empty'])
    def test_search_movies_empty_results(self, search_api, empty_case):
        """
        Test searching movies with a missing, empty or unmatched query.

        TMDB returns 200 with an empty results page for these requests
        rather than an error, so the test asserts the empty pagination
        body directly (the search schema requires at least one result,
        so it does not apply here).

        :param search_api: SearchAPI client fixture from conftest.py.
        :param empty_case: Parametrized test data containing a query_param
                           that yields no matches and expected status_code.
        """
        allure.dynamic.title(f"Search movies with no matches for query params: {empty_case['query_param']}")
        logger.info(f"Testing search_movies with no expected matches for query params: {empty_case['query_param']}")
        with allure.step(f"Send GET request to search movies"):
            response = search_api.search_movies(query_params=empty_case['query_param'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, empty_case, 'search/movie')

        with allure.step("Validate empty paginated results"):
            assert res_body['results'] == []
            assert res_body['total_results'] == 0

    @allure.story("Search Movies with Invalid Query Params")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('invalid_test', TEST_DATA['search_movies']['invalid'])
    def test_search_movies_invalid(self, search_api, load_schema, invalid_test):
        """
        Test searching movies with invalid parameters.

        Validates that appropriate error responses are returned when
        invalid query parameters are provided for the search movie endpoint.

        :param search_api: SearchAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_test: Parametrized test data containing invalid query_param,
                             expected status_code, and expected_message.
        """
        allure.dynamic.title(f"Search movies with invalid query params: {invalid_test['query_param']}")
        logger.info(f"Testing search_movies with invalid query params: {invalid_test['query_param']}")
        with allure.step(f"Send GET request to search movies"):
            response = search_api.search_movies(query_params=invalid_test['query_param'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, invalid_test, 'search/movie')

        with allure.step("Validate error message"):
            assert res_body['status_message'] == invalid_test['expected_message']

        with allure.step("Validate response structure & schema (GenericResponse)"):
            load_schema('generic_schema').model_validate(res_body)
