"""
Test suite for the Movies API endpoints.

This module contains integration tests for the MoviesAPI class, validating
both successful responses and error handling. Tests are data-driven using
external YAML test data files with pytest's parametrize decorator.

Test data is loaded from 'test_data.yaml' which contains valid and
invalid test cases with expected values and defaults applied.

Dependencies:
    - pytest: Test framework
    - jsonschema: Response structure validation
    - MoviesAPI: API client under test
    - load_test_data: YAML test data loader

Usage:
    pytest tests/test_movies.py -v
"""

import pytest
from jsonschema import validate
from loguru import logger

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml")
"""Module-level test data loaded once at import time for parametrization."""

class TestDetails(FieldAssertions):
    """
    Test class for Movies API endpoint validation.

    Contains tests for the get_movie_details endpoint covering both
    valid requests and error scenarios. Each test validates HTTP
    method, status codes, headers, response time, and body structure.
    """
    @pytest.fixture(autouse=True)
    def _store_test_name(self, request):
        """
        Fixture to capture and store the current test name.

        Automatically runs before each test method (autouse=True) and stores
        the test name in self._test_name for use in assertion messages.

        :param request: Pytest request fixture providing test context.
        """
        self._test_name = request.node.name

    @pytest.mark.parametrize('movie_details', TEST_DATA['get_movie_details']['valid'])
    def test_get_movie_details(self, get_api_instance, load_schema, movie_details):
        """
        Test error handling for invalid movie IDs.

        Validates proper error responses when requesting non-existent
        or invalid movie IDs, ensuring appropriate status codes and
        error messages are returned.

        :param get_api_instance: Generic class fixture instance.
        :param load_schema: Schema loader fixture from conftest.py.
        :param movie_details: Parametrized test data containing valid movie_id,
                             expected status_code, and expected_message.
        """
        movie_id = movie_details['movie_id']
        logger.info(f"Running test: {self._test_name} for movie_id: {movie_id}")
        movies_api = get_api_instance('movies_api')
        response = movies_api.get_movie_details(movie_id)
        res_body = response.data

        # Basic response validations
        assert_http_response(response, {
            'exp_status_code': movie_details['status_code'],
            'exp_max_elp_seconds': movie_details['exp_max_elp_secs'],
            'exp_req_method': movie_details['exp_get_req_method'],
            'exp_content_type': movie_details['exp_content_type'],
            'exp_url_contains': str(movie_id),
            'exp_req_reason': movie_details['reason']
        })

        # response structure validation
        self.assert_list_field(res_body, 'genres')
        self.assert_list_field(res_body, 'origin_country')
        self.assert_list_field(res_body, 'production_companies')

        if len(res_body['genres']) > 0:
            for idx, it in enumerate(res_body['genres']):
                self.assert_int_field(it, 'id', idx)
                self.assert_str_field(it, 'name', idx)

        self.assert_int_field(res_body, 'id')
        self.assert_bool_field(res_body, 'adult')
        self.assert_str_field(res_body, 'original_language')
        self.assert_str_field(res_body, 'title')
        self.assert_str_field(res_body, 'original_title')

        if len(res_body['production_companies']) > 0:
            for idx, it in enumerate(res_body['production_companies']):
                self.assert_int_field(it, 'id', idx)
                self.assert_path_field(it, 'logo_path', idx)
                self.assert_str_field(it, 'name', idx)
                self.assert_str_field(it, 'origin_country', idx)

        # load_schema is a fixture from conftest.py
        # Validate response against JSON schema
        validate(instance=res_body, schema=load_schema('movie_schema'))

    @pytest.mark.parametrize('invalid_test', TEST_DATA['get_movie_details']['invalid'])
    def test_get_invalid_movie_details(self, get_api_instance, load_schema, invalid_test):
        """
        Test error handling for invalid movie IDs.

        Validates proper error responses when requesting non-existent
        or invalid movie IDs, ensuring appropriate status codes and
        error messages are returned.

        :param get_api_instance: Generic fixture instance.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_test: Parametrized test data containing invalid movie_id,
                             expected status_code, and expected_message.
        """
        movie_id = invalid_test['movie_id']
        logger.info(f"Testing invalid movie_id: {movie_id}")
        movies_api = get_api_instance('movies_api')
        response = movies_api.get_movie_details(movie_id)
        res_body = response.data

        assert_http_response(response, {
            'exp_status_code': invalid_test['status_code'],
            'exp_max_elp_seconds': invalid_test['exp_max_elp_secs'],
            'exp_req_method': invalid_test['exp_get_req_method'],
            'exp_content_type': invalid_test['exp_content_type'],
            'exp_url_contains': str(movie_id),
            'exp_req_reason': invalid_test['reason']
        })
        assert res_body['status_message'] == invalid_test['expected_message']

        validate(instance=res_body, schema=load_schema('generic_invalid_schema'))