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

    @pytest.fixture(autouse=True)
    def _store_test_name(self, request):
        """
        Fixture to capture and store the current test name.

        Automatically runs before each test method (autouse=True) and stores
        the test name in self._test_name for use in assertion messages.

        :param request: Pytest request fixture providing test context.
        """
        self._test_name = request.node.name

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
                assert it['origin_country'] is None or len(
                    it['origin_country']) > 0, "Origin Country should not be empty"

        # Validate response against JSON schema
        validate(instance=res_body, schema=load_schema('movie_schema'))

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

    def test_get_popular_movies_default(self, movies_api, load_schema, request):
        """
        Test retrieving popular movies with default parameters.

        Validates that the default page of popular movies is returned
        correctly, including response structure and content.

        :param movies_api: MoviesAPI fixture instance.
        :param load_schema: Schema loader fixture from conftest.py.
        """
        response = movies_api.get_popular_movies(query_params={"language": "en-US"})
        res_body = response.data

        assert response.request == 'GET', 'HTTP method is not GET'
        assert response.status_code == 200, 'returned status code is not 200'
        assert 'application/json' in response.headers['Content-Type'], 'response is not in JSON format'
        assert response.elapsed_seconds < 2, 'response time is too long'
        assert 'popular' in response.url, "Response url should contain 'popular'"

        # response structure validation
        assert isinstance(res_body['page'], int), f"{self._test_name}: Page Response should be int"
        assert res_body['page'] > 0, f"{self._test_name}: Page should be positive"

        assert isinstance(res_body['results'], list), f"{self._test_name}: Page Results should be a list"
        assert len(res_body['results']) > 0, f"P{self._test_name}: age results should not be empty"
        for idx, it in enumerate(res_body['results']):
            assert 'genre_ids' in it, f"{self._test_name}: results at index {idx} should contain 'genre_ids' field"
            assert isinstance(it['genre_ids'], list), f"{self._test_name}: genre_ids should be a list"

            self.assert_bool_field(it, 'adult', idx)
            self.assert_bool_field(it, 'video', idx)

            self.assert_path_field(it, 'backdrop_path', idx)
            self.assert_path_field(it, 'poster_path', idx)

            self.assert_int_field(it, 'id', idx)
            self.assert_int_field(it, 'vote_count', idx)

            self.assert_str_field(it, 'original_title', idx)
            self.assert_str_field(it, 'overview', idx)
            self.assert_str_field(it, 'title', idx)
            self.assert_str_field(it, 'release_date', idx)
            self.assert_str_field(it, 'original_language', idx)

            self.assert_float_field(it, 'popularity', idx)
            self.assert_float_field(it, 'vote_average', idx)

        # Validate response against JSON schema
        validate(instance=res_body, schema=load_schema('popular_movies_schema'))

    # Helpers

    def assert_bool_field(self, data, field, index=None):
        """
        Assert that a field value is a boolean.

        :param data: Dictionary containing the field to validate.
        :param field: Name of the field to check.
        :param index: Optional array index for contextual error messages.
        :raises AssertionError: If the field is not a boolean.
        """
        idx = f'{index}' if index is not None else ''
        assert isinstance(data[field], bool), f"{self._test_name}: Index {idx} {field} Response should be boolean"

    def assert_str_field(self, data, field, index=None):
        """
        Assert that a field value is a non-empty string.

        For 'original_language' fields, validates 2-character ISO code length.

        :param data: Dictionary containing the field to validate.
        :param field: Name of the field to check.
        :param index: Optional array index for contextual error messages.
        :raises AssertionError: If the field is not a string or is empty.
        """
        idx = f'{index}' if index is not None else ''
        assert isinstance(data[field], str), f"{self._test_name}: Index {idx} {field} Response should be string"

        if data[field] == 'original_language':
            assert len(data[field]) == 2, f"{self._test_name}: Index {idx} {field} should be 2-char code"
        else:
            assert len(data[field]) > 0, f"{self._test_name}: Index {idx} {field} should not be empty"

    def assert_int_field(self, data, field, index=None):
        """
        Assert that a field value is a positive integer.

        :param data: Dictionary containing the field to validate.
        :param field: Name of the field to check.
        :param index: Optional array index for contextual error messages.
        :raises AssertionError: If the field is not an integer or not positive.
        """
        idx = f'{index}' if index is not None else ''
        assert isinstance(data[field], int), f"{self._test_name}: Index {idx} {field} Response should be int"
        assert data[field] > 0, f"{self._test_name}: Index {idx} {field} should be non-negative"

    def assert_path_field(self, data, field, index=None):
        """
        Assert that a field is a valid image path or null.

        Validates that the path ends with '.png' or '.jpg' if not null.

        :param data: Dictionary containing the field to validate.
        :param field: Name of the field to check.
        :param index: Optional array index for contextual error messages.
        :raises AssertionError: If field is missing or has invalid format.
        """
        idx = f'{index}' if index is not None else ''
        assert field in data, f"{self._test_name}: Index {idx} should contain '{field}' field"
        assert data[field] is None or isinstance(data[field],
                                                 str), f"{self._test_name}: Index {idx} {field} should be String"
        assert data[field] is None or data[field].endswith(
            ('.png', '.jpg')), f'{self._test_name}: Index {idx} {field} should be PNG'

    def assert_float_field(self, data, field, index=None):
        """
        Assert that a field value is a positive float.

        For 'vote_average' fields, validates range is 0.0-10.0.

        :param data: Dictionary containing the field to validate.
        :param field: Name of the field to check.
        :param index: Optional array index for contextual error messages.
        :raises AssertionError: If the field is not a float or out of range.
        """
        idx = f'{index}' if index is not None else ''
        assert isinstance(data[field], float), f"{self._test_name}: Index {idx} {field} Response should be float"

        if data[field] == 'vote_average':
            assert 0.0 <= data[field] <= 10.0, f"{self._test_name}: Index {idx} {field} should be between 0.0 and 10.0"
        else:
            assert data[field] > 0.0, f"{self._test_name}: Index {idx} {field} should be positive"