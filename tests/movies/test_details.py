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
from loguru import logger

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml")
"""Module-level test data loaded once at import time for parametrization."""

@allure.epic("TMDB API")
@allure.feature("Movies")
class TestDetails(FieldAssertions):
    """
    Test class for Movies API endpoint validation.

    Contains tests for the get_movie_details endpoint covering both
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

    @allure.story("Get Movie Details")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('movie_details', TEST_DATA['get_movie_details']['valid'])
    def test_get_movie_details(self, movies_api, load_schema, movie_details):
        """
        Test successful retrieval of movie details for valid movie IDs.

        Validates the response for existing movie IDs, ensuring the
        expected status code, HTTP metadata, response structure, and
        Pydantic schema all match for a valid request.

        :param movies_api: MoviesAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param movie_details: Parametrized test data containing valid movie_id,
                             expected status_code, and expected_message.
        """
        movie_id = movie_details['movie_id']
        allure.dynamic.title(f"Get movie details for ID: {movie_id}")
        logger.info(f"Running test: {self._test_name} for movie_id: {movie_id}")

        with allure.step(f"Send GET request for movie {movie_id}"):
            response = movies_api.get_movie_details(movie_id)
            res_body = response.data

        # Basic response validations
        with allure.step("Validate HTTP response metadata"):
            self._assert_get_metadata(response, movie_details, movie_id)

        # Structure, types, and field semantics (presence, strict types,
        # non-empty/ISO/path rules, nested genres & production_companies, and
        # empty-list handling) are all enforced by the MovieDetails model.
        # load_schema is a fixture from conftest.py
        with allure.step("Validate response structure & schema (MovieDetails)"):
            load_schema('movie_schema').model_validate(res_body)

    @allure.story("Get Movie Details - Invalid")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('invalid_test', TEST_DATA['get_movie_details']['invalid'])
    def test_get_invalid_movie_details(self, movies_api, load_schema, invalid_test):
        """
        Test error handling for invalid movie IDs.

        Validates proper error responses when requesting non-existent
        or invalid movie IDs, ensuring appropriate status codes and
        error messages are returned.

        :param movies_api: MoviesAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_test: Parametrized test data containing invalid movie_id,
                             expected status_code, and expected_message.
        """
        movie_id = invalid_test['movie_id']
        allure.dynamic.title(f"Invalid movie ID: {movie_id}")
        logger.info(f"Testing invalid movie_id: {movie_id}")

        with allure.step(f"Send GET request for invalid movie ID {movie_id}"):
            response = movies_api.get_movie_details(movie_id)
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            self._assert_get_metadata(response, invalid_test, movie_id)

        with allure.step("Validate error message"):
            assert res_body['status_message'] == invalid_test['expected_message']

        # GenericResponse (strict, extra="forbid") enforces the error body's
        # structure and types; only the message value is asserted above.
        with allure.step("Validate response structure & schema (GenericResponse)"):
            load_schema('generic_schema').model_validate(res_body)