import pytest
from jsonschema import validate
from loguru import logger

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml")
"""Module-level test data loaded once at import time for parametrization."""

class TestAddRating(FieldAssertions):
    """
    Test class for Movies API add_rating endpoint validation.

    Contains tests for the add_rating endpoint covering both valid
    requests and error scenarios. Each test validates HTTP method,
    status codes, headers, response time, and body structure.
    """

    @pytest.mark.order(1)
    @pytest.mark.parametrize('add_valid_rating', TEST_DATA['add_rating']['valid'])
    def test_add_rating(self, get_api_instance, load_schema, add_valid_rating):
        """
        Test adding a movie rating without authentication.

        Validates that attempting to add a rating without proper
        authentication returns the expected error response.

        :param get_api_instance: Generic fixture instance.
        :param load_schema: Schema loader fixture from conftest.py.
        :param add_valid_rating: Parametrized test data containing valid movie_id,
                                   expected status_code, and expected_message.
        """
        movie_id = pick_random_movie_id()
        rating = add_valid_rating['rating_payload']['value']
        logger.info(f"Testing add_rating for movie_id: {movie_id} with rating: {rating}")
        movies_api = get_api_instance('movies_api')
        response = movies_api.add_rating(movie_id, rating, query_params=Config.SESSION_ID)
        res_json = response.data

        assert_http_response(response, {
            'exp_status_code': add_valid_rating['status_code'],
            'exp_max_elp_seconds': add_valid_rating['exp_max_elp_secs'],
            'exp_req_method': add_valid_rating['exp_post_req_method'],
            'exp_content_type': add_valid_rating['exp_content_type'],
            'exp_url_contains': str(movie_id),
            'exp_req_reason': add_valid_rating['reason']
        })

        self.assert_bool_field(res_json, 'success')
        self.assert_int_field(res_json, 'status_code')
        self.assert_str_field(res_json, 'status_message')

        if 'success' in res_json:
            assert res_json['success'] is True, "Rating should be added successfully. Its false now"
            validate(instance=res_json, schema=load_schema('add_delete_rating_schema'))

    @pytest.mark.parametrize('add_invalid_rating', TEST_DATA['add_rating']['invalid'])
    def test_add_rating_unauthenticated(self, load_schema, get_api_instance, add_invalid_rating):
        """
        Test adding a movie rating without authentication.

        Validates that attempting to add a rating without proper
        authentication returns the expected error response.

        :param get_api_instance: Generic fixture instance.
        :param add_invalid_rating: Parametrized test data containing invalid movie_id,
                                   expected status_code, and expected_message.
        """
        movie_id = add_invalid_rating['movie_id']
        rating = add_invalid_rating['rating_payload']['value']
        logger.info(f"Testing add_rating for movie_id: {movie_id} with invalid rating: {rating}")
        movies_api = get_api_instance('movies_api')
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

        validate(instance=res_json, schema=load_schema('generic_invalid_schema'))