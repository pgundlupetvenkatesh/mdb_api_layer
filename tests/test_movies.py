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

from config.config import Config
from api.movies_api import MoviesAPI
from .data.data_loader import load_test_data
from .helpers import *

TEST_DATA = load_test_data("movies_test_data.yaml")
"""Module-level test data loaded once at import time for parametrization."""

class TestMoviesAPI(FieldAssertions):
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
        :param test_case: Parametrized test data containing valid movie_id,
                             expected status_code, and expected_message.
        """

        # movies_api creates MoviesAPI() instance
        # load_schema is a fixture from conftest.py

        movie_id = test_case['movie_id']
        print(f"Running test: {self._test_name} for movie_id: {movie_id}")
        response = movies_api.get_movie_details(movie_id)
        res_body = response.data

        # Basic response validations
        assert_http_response(response, {
            'exp_status_code': test_case['status_code'],
            'exp_max_elp_seconds': test_case['exp_max_elp_secs'],
            'exp_req_method': test_case['exp_get_req_method'],
            'exp_content_type': test_case['exp_content_type'],
            'exp_url_contains': str(movie_id),
            'exp_req_reason': test_case['reason']
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
        assert res_body['original_language'] == test_case['original_language'], f"Movie ID should be {movie_id}"
        assert res_body['title'] == test_case['movie_title'], "Response should contain 'title' field"

        if len(res_body['production_companies']) > 0:
            for idx, it in enumerate(res_body['production_companies']):
                self.assert_int_field(it, 'id', idx)

                self.assert_path_field(it, 'logo_path', idx)

                self.assert_str_field(it, 'name', idx)
                self.assert_str_field(it, 'origin_country', idx)

        # Validate response against JSON schema
        validate(instance=res_body, schema=load_schema('movie_schema'))

    @pytest.mark.parametrize('pop_movies', TEST_DATA['popular_movies']['valid'])
    def test_get_popular_movies_default(self, movies_api, load_schema, pop_movies):
        """
        Test retrieving popular movies with default parameters.

        Validates that the default page of popular movies is returned
        correctly, including response structure and content.

        :param movies_api: MoviesAPI fixture instance.
        :param load_schema: Schema loader fixture from conftest.py.
        """
        response = movies_api.get_popular_movies(query_params=pop_movies['query_param'])
        res_body = response.data

        assert_http_response(response, {
            'exp_status_code': pop_movies['status_code'],
            'exp_max_elp_seconds': pop_movies['exp_max_elp_secs'],
            'exp_req_method': pop_movies['exp_get_req_method'],
            'exp_content_type': pop_movies['exp_content_type'],
            'exp_url_contains': 'popular',
            'exp_req_reason': pop_movies['reason']
        })

        # response structure validation
        self.assert_int_field(res_body, 'total_results', response.request_params['page'])

        self.assert_list_field(res_body, 'results')

        for idx, it in enumerate(res_body['results']):
            self.assert_list_field(it, 'genre_ids', idx)

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

    @pytest.mark.parametrize('add_valid_rating', TEST_DATA['add_rating']['valid'])
    def test_add_rating(self, movies_api, load_schema, add_valid_rating):
        """
        Test adding a movie rating without authentication.

        Validates that attempting to add a rating without proper
        authentication returns the expected error response.

        :param movies_api: MoviesAPI fixture instance.
        """
        movie_id = pick_random_movie_id()
        rating = add_valid_rating['rating_payload']['value']
        print(f"Testing add_rating for movie_id: {movie_id} with rating: {rating}")
        response = movies_api.add_rating(movie_id, rating, query_params=Config.SESSION_ID)
        res_json = response.data

        assert_http_response(response, {
            'exp_status_code': add_valid_rating['status_code'],
            'exp_max_elp_seconds': add_valid_rating['exp_max_elp_secs'],
            'exp_req_method':  add_valid_rating['exp_post_req_method'],
            'exp_content_type':  add_valid_rating['exp_content_type'],
            'exp_url_contains': str(movie_id),
            'exp_req_reason': add_valid_rating['reason']
        })

        self.assert_bool_field(res_json, 'success')
        self.assert_int_field(res_json, 'status_code')
        self.assert_str_field(res_json, 'status_message')

        if 'success' in res_json:
            assert res_json['success'] is True, "Rating should be added successfully. Its false now"
            validate(instance=res_json, schema=load_schema('add_rating_schema'))

    # Invalid test cases

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
        movie_id = invalid_test['movie_id']
        print(f"Testing invalid movie_id: {movie_id}")
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

    @pytest.mark.parametrize('invalid_test', TEST_DATA['popular_movies']['invalid'])
    def test_get_popular_movies_invalid(self, movies_api, load_schema, invalid_test):
        """
        Test retrieving popular movies with invalid parameters.

        Validates that appropriate error responses are returned when
        invalid query parameters are provided for the popular movies
        endpoint.

        :param movies_api: MoviesAPI fixture instance.
        :param load_schema: Schema loader fixture from conftest.py.
        """
        response = movies_api.get_popular_movies(query_params=invalid_test['query_param'])
        res_body = response.data

        assert_http_response(response, {
            'exp_status_code': invalid_test['status_code'],
            'exp_max_elp_seconds': invalid_test['exp_max_elp_secs'],
            'exp_req_method': invalid_test['exp_get_req_method'],
            'exp_content_type': invalid_test['exp_content_type'],
            'exp_url_contains': 'popular',
            'exp_req_reason': invalid_test['reason']
        })
        assert res_body['status_message'] == invalid_test['expected_message']

    @pytest.mark.parametrize('add_invalid_rating', TEST_DATA['add_rating']['invalid'])
    def test_add_rating_unauthenticated(self, movies_api, add_invalid_rating):
        """
        Test adding a movie rating without authentication.

        Validates that attempting to add a rating without proper
        authentication returns the expected error response.

        :param movies_api: MoviesAPI fixture instance.
        """
        movie_id = add_invalid_rating['movie_id']
        rating = add_invalid_rating['rating_payload']['value']
        print(f"Testing add_rating for movie_id: {movie_id} with invalid rating: {rating}")
        response = movies_api.add_rating(movie_id, rating, query_params=Config.SESSION_ID)
        res_json = response.data

        assert_http_response(response, {
            'exp_status_code': add_invalid_rating['status_code_bad_req'],
            'exp_max_elp_seconds': add_invalid_rating['exp_max_elp_secs'],
            'exp_req_method': add_invalid_rating['exp_post_req_method'],
            'exp_content_type': add_invalid_rating['exp_content_type'],
            'exp_url_contains': str(movie_id),
            'exp_req_reason': add_invalid_rating['reason']
        })
        assert res_json['status_message'] in add_invalid_rating['expected_message'], \
            f"Unexpected message: '{res_json['status_message']}' not in {add_invalid_rating['expected_message']}"