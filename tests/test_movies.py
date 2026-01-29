"""
Test suite for the Movies API endpoints.

This module contains integration tests for the MoviesAPI class, validating
both successful responses and error handling. Tests are data-driven using
external YAML test data files with pytest's parametrize decorator.

Test data is loaded from 'movies_test_data.yaml' which contains valid and
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

from api.movies_api import MoviesAPI
from tests.data.data_loader import load_test_data

TEST_DATA = load_test_data("movies_test_data.yaml")
"""Module-level test data loaded once at import time for parametrization."""

class TestMoviesAPI:
    """
    Test class for Movies API endpoint validation.

    Contains tests for the get_movie_details endpoint covering both
    valid requests and error scenarios. Each test validates HTTP
    method, status codes, headers, response time, and body structure.
    """

    @pytest.fixture
    def movies_api(self):
        """
        Fixture that provides a MoviesAPI instance for each test.

        Creates a fresh API client before each test and yields it for use.
        Cleanup logic can be added after the yield statement if needed.

        :yields: Configured MoviesAPI instance.
        """
        api = MoviesAPI()
        yield api  # Test runs here
        # api.close()  # Cleanup after test

    @pytest.mark.parametrize('test_case', TEST_DATA['get_movie_details']['valid'])
    def test_get_movie_details(self, movies_api, load_schema, test_case):
        """
        Test error handling for invalid movie IDs.

        Validates proper error responses when requesting non-existent
        or invalid movie IDs, ensuring appropriate status codes and
        error messages are returned.

        :param movies_api: MoviesAPI fixture instance.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_test: Parametrized test data containing invalid movie_id,
                             expected status_code, and expected_message.
        """

        # movies_api creates MoviesAPI() instance
        # load_schema is a fixture from conftest.py

        movie_id = test_case['movie_id']  # Example movie ID for "Fight Club"
        response = movies_api.get_movie_details(movie_id)
        res_body = response.data

        # Basic response validations
        assert response.request == 'GET', 'HTTP method is not GET'
        assert response.status_code == test_case['status_code'], 'returned status code is not 200'
        assert 'application/json' in response.headers['Content-Type'], 'response is not in JSON format'
        assert response.elapsed_seconds < 2, 'response time is too long'
        assert str(movie_id) in response.url, f"Response url should contain movie ID '{movie_id}'"

        # response structure validation
        assert isinstance(res_body['genres'], list), "Genres should be a list"
        if len(res_body['genres']) > 0:
            for idx, it in enumerate(res_body['genres']):
                assert 'id' in it, f"Genre at index {idx} should contain 'id' field"
                assert isinstance(it['id'], int), "Genres Id should be int"
                assert it['id'] > 0, "Genres Id should be positive"

                assert 'name' in it, f"Genre at index {idx} should contain 'name' field"
                assert isinstance(it['name'], str), "Genres name Id should be String"
                assert len(it['name']) > 0, "Genres name should not be empty"

        assert isinstance(res_body['id'], int), "Id Response should be int"
        assert res_body['id'] > 0, "Id should be positive"
        assert res_body['id'] == movie_id, f"Movie ID should be {movie_id}"

        assert isinstance(res_body['adult'], bool), "Adult Response should be boolean"

        assert isinstance(res_body['origin_country'], list), "Origin Country Response should be a list"
        assert len(res_body['origin_country']) > 0, "Origin Country should not be empty"

        assert isinstance(res_body['original_language'], str), "Origin language Response should be string"
        assert len(res_body['original_language']) == 2, "Original language should be 2-char code"
        assert res_body['original_language'] == test_case['original_language'], f"Movie ID should be {movie_id}"

        assert isinstance(res_body['title'], str), "Title Response should be string"
        assert len(res_body['title']) > 0, "Title should not be empty"
        assert 'title' in res_body, "Response should contain 'title' field"
        assert res_body['title'] == test_case['movie_title'], "Response should contain 'title' field"

        assert isinstance(res_body['original_title'], str), "Original Title Response should be string"
        assert len(res_body['original_title']) > 0, "Original Title should not be empty"

        assert isinstance(res_body['production_companies'], list), "Production Companies Response should be a list"
        if len(res_body['production_companies']) > 0:
            for idx, it in enumerate(res_body['production_companies']):
                assert 'id' in it, f"Production Company at index {idx} should contain 'id' field"
                assert isinstance(it['id'], int), "Production Companies Id should be int"
                assert it['id'] > 0, "Id should be positive"

                assert 'logo_path' in it, f"Production Company at index {idx} should contain 'logo path' field"
                assert it['logo_path'] is None or isinstance(it['logo_path'],
                                  str), f"Production Companies at index {idx} Logo Path should be String"
                assert it['logo_path'] is None or it['logo_path'].endswith(
                    ('.png', '.jpg')), 'Production Companies Logo Path should be PNG'

                assert 'name' in it, f"Production Company at index {idx} should contain 'name' field"
                assert isinstance(it['name'], str), "Production Companies name should be String"
                assert len(it['name']) > 0, "Production Companies name should not be empty"

                assert 'origin_country' in it, f"Production Company at index {idx} should contain 'origin country' field"
                assert isinstance(it['origin_country'], str), "Production Companies Origin Country should be String"
                assert it['origin_country'] is None or len(it['origin_country']) > 0, "Origin Country should not be empty"

        # Validate response against JSON schema
        validate(instance=response.data, schema=load_schema('movie_schema'))

    @pytest.mark.parametrize('invalid_test', TEST_DATA['get_movie_details']['invalid'])
    def test_get_invalid_movie_details(self, movies_api, load_schema, invalid_test):
        """
        Test error handling for invalid movie IDs.

        Validates proper error responses when requesting non-existent
        or invalid movie IDs, ensuring appropriate status codes and
        error messages are returned.

        :param movies_api: MoviesAPI fixture instance.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_test: Parametrized test data containing invalid movie_id,
                             expected status_code, and expected_message.
        """
        movie_id = invalid_test['movie_id']  # Invalid movie ID
        response = movies_api.get_movie_details(movie_id)
        res_body = response.data

        assert response.request == 'GET', 'HTTP method is not GET'
        assert response.status_code == invalid_test['status_code'], 'returned error status code is not 404'
        assert 'application/json' in response.headers['Content-Type'], 'response is not in JSON format'
        assert response.elapsed_seconds < 2, 'response time is too long'
        assert str(movie_id) in response.url, f"Response url should contain movie ID '{movie_id}'"
        assert res_body['status_message'] == invalid_test['expected_message']
