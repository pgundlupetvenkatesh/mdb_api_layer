"""
Test suite for the Movies API endpoints.

This module contains integration tests for the MoviesAPI class, validating
both successful responses and error handling. Tests are data-driven using
external YAML test data files with pytest's parametrize decorator.

Test data is loaded from 'test_data.yaml' which contains valid and
invalid test cases with expected values and defaults applied.

Dependencies:
    - pytest: Test framework
    - pydantic: Response structure validation
    - MoviesAPI: API client under test
    - load_test_data: YAML test data loader

Usage:
    pytest tests/test_popular.py -v
"""

import allure
import pytest

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml", "popular_movies")
"""Module-level test data loaded once at import time for parametrization."""

@allure.epic("TMDB API")
@allure.feature("Movie Lists")
class TestMoviesAPI(FieldAssertions):
    """
    Test class for Movies API endpoint validation.

    Contains tests for the get_popular_movies endpoint covering both
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

    @allure.story("Get Popular Movies")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('pop_movies', TEST_DATA['popular_movies']['valid'])
    def test_get_popular_movies_default(self, movies_api, load_schema, pop_movies):
        """
        Test retrieving popular movies with default parameters.

        Validates that the default page of popular movies is returned
        correctly, including response structure and content.

        :param movies_api: MoviesAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py
        :param pop_movies: Parametrized test data containing valid query_param,
                           expected status_code, and expected_message.
        """
        allure.dynamic.title(f"Get popular movies with query params: {pop_movies['query_param']}")
        with allure.step(f"Send GET request for popular movies"):
            response = movies_api.get_popular_movies(query_params=pop_movies['query_param'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            self._assert_get_metadata(response, pop_movies, 'popular')

        # PopularMoviesResponse (strict) enforces pagination fields plus every
        # item's structure, types, and field semantics (non-empty results,
        # strict types, ISO/path/range rules).
        with allure.step("Validate response structure & schema (PopularMoviesResponse)"):
            load_schema('popular_movies_schema').model_validate(res_body)

    @allure.story("Get Popular Movies with Invalid Query Params")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('invalid_test', TEST_DATA['popular_movies']['invalid'])
    def test_get_popular_movies_invalid(self, movies_api, load_schema, invalid_test):
        """
        Test retrieving popular movies with invalid parameters.

        Validates that appropriate error responses are returned when
        invalid query parameters are provided for the popular movies endpoint.

        :param movies_api: MoviesAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_test: Parametrized test data containing invalid query_param,
                             expected status_code, and expected_message.
        """
        allure.dynamic.title(f"Get invalid popular movies with query params: {invalid_test['query_param']}")
        with allure.step(f"Send GET request for popular movies"):
            response = movies_api.get_popular_movies(query_params=invalid_test['query_param'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            self._assert_get_metadata(response, invalid_test, 'popular')

        with allure.step("Validate error message"):
            assert res_body['status_message'] == invalid_test['expected_message']

        with allure.step("Validate response structure & schema (GenericResponse)"):
            load_schema('generic_schema').model_validate(res_body)