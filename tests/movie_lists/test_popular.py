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
    pytest tests/test_popular.py -v
"""

import allure
import pytest

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml")
"""Module-level test data loaded once at import time for parametrization."""

@allure.epic("TMDB API")
@allure.feature("Movie Lists")
class TestMoviesAPI(FieldAssertions):
    """
    Test class for Movies API endpoint validation.

    Contains tests for the get_movie_details endpoint covering both
    valid requests and error scenarios. Each test validates HTTP
    method, status codes, headers, response time, and body structure.
    """

    @allure.story("Get Popular Movies")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('pop_movies', TEST_DATA['popular_movies']['valid'])
    def test_get_popular_movies_default(self, get_api_instance, load_schema, pop_movies):
        """
        Test retrieving popular movies with default parameters.

        Validates that the default page of popular movies is returned
        correctly, including response structure and content.

        :param get_api_instance: Generic fixture instance.
        :param load_schema: Schema loader fixture from conftest.py
        :param pop_movies: Parametrized test data containing valid query_param,
                           expected status_code, and expected_message.
        """
        movies_api = get_api_instance('movies_api')
        allure.dynamic.title(f"Get popular movies with query params: {pop_movies['query_param']}")
        with allure.step(f"Send GET request for popular movies"):
            response = movies_api.get_popular_movies(query_params=pop_movies['query_param'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_http_response(response, {
                'exp_status_code': pop_movies['status_code'],
                'exp_max_elp_seconds': pop_movies['exp_max_elp_secs'],
                'exp_req_method': pop_movies['exp_get_req_method'],
                'exp_content_type': pop_movies['exp_content_type'],
                'exp_url_contains': 'popular',
                'exp_req_reason': pop_movies['reason']
            })

        # response structure validation
        with allure.step("Validate response structure"):
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
        with allure.step("Validate against Pydantic schema"):
            load_schema('popular_movies_schema').model_validate(res_body)

    @allure.story("Get Popular Movies with Invalid Query Params")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('invalid_test', TEST_DATA['popular_movies']['invalid'])
    def test_get_popular_movies_invalid(self, get_api_instance, load_schema, invalid_test):
        """
        Test retrieving popular movies with invalid parameters.

        Validates that appropriate error responses are returned when
        invalid query parameters are provided for the popular movies endpoint.

        :param get_api_instance: Generic fixture instance.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_test: Parametrized test data containing invalid query_param,
                             expected status_code, and expected_message.
        """
        movies_api = get_api_instance('movies_api')
        allure.dynamic.title(f"Get invalid popular movies with query params: {invalid_test['query_param']}")
        with allure.step(f"Send GET request for popular movies"):
            response = movies_api.get_popular_movies(query_params=invalid_test['query_param'])
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_http_response(response, {
                'exp_status_code': invalid_test['status_code'],
                'exp_max_elp_seconds': invalid_test['exp_max_elp_secs'],
                'exp_req_method': invalid_test['exp_get_req_method'],
                'exp_content_type': invalid_test['exp_content_type'],
                'exp_url_contains': 'popular',
                'exp_req_reason': invalid_test['reason']
            })
            assert res_body['status_message'] == invalid_test['expected_message']

        with allure.step("Validate against Pydantic schema"):
            load_schema('generic_schema').model_validate(res_body)