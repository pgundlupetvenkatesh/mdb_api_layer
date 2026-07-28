"""
Test suite for the Reviews API details endpoint.

This module contains integration tests for the ReviewsAPI class, validating
both successful responses and error handling for ``GET /3/review/{review_id}``.
Tests are data-driven using external YAML test data files with pytest's
parametrize decorator.

Test data is loaded from 'test_data.yaml' which contains valid and invalid
test cases with expected values and defaults applied. The valid review ID is
harvested live at collection time from a random movie's reviews via the
``$random_review_id`` generator.

Dependencies:
    - pytest: Test framework
    - pydantic: Response structure validation
    - ReviewsAPI: API client under test
    - load_test_data: YAML test data loader

Usage:
    pytest tests/reviews/test_details.py -v
"""

import allure
import pytest

from loguru import logger
from tests.data.data_loader import load_test_data
from tests.helpers import *

TEST_DATA = load_test_data("test_data.yaml", "get_review_details")
"""Module-level test data loaded once at import time for parametrization."""

@allure.epic("TMDB API")
@allure.feature("Reviews")
class TestDetails(FieldAssertions):
    """
    Test class for Reviews API get_review_details endpoint validation.

    Contains tests for the get_review_details endpoint covering both
    valid requests and error scenarios. Each test validates HTTP
    method, status codes, headers, response time, and body structure.
    """

    @allure.story("Get Review Details")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('review_details', TEST_DATA['get_review_details']['valid'])
    def test_get_review_details(self, reviews_api, load_schema, review_details):
        """
        Test fetching review details with a valid review ID.

        Validates that the response returns the expected 200 status, correct
        HTTP metadata, the requested review ID echoed in the body, and a
        body that conforms to the strict ReviewDetails schema.

        :param reviews_api: ReviewsAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param review_details: Parametrized test data containing a valid
                               review_id, expected status_code, and reason.
        """
        review_id = review_details['review_id']
        logger.info(f"Review ID picked: {review_id}")
        allure.dynamic.title(f"Get details for review ID: {review_id}")

        with allure.step(f"Send GET request for review ID {review_id}"):
            response = reviews_api.get_review_details(review_id)
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, review_details, 'review')

        with allure.step("Validate requested review ID is echoed in the response"):
            assert res_body['id'] == review_id

        # ReviewDetails (strict) enforces the body structure, types, and field
        # semantics (strict types, nested author_details, no extra fields).
        with allure.step("Validate response structure & schema (ReviewDetails)"):
            load_schema('review_details_schema').model_validate(res_body)

    @allure.story("Get Invalid Review Details")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('invalid_review_details', TEST_DATA['get_review_details']['invalid'])
    def test_get_review_details_invalid(self, reviews_api, load_schema, invalid_review_details):
        """
        Test fetching review details with an invalid review ID.

        Validates that the API returns the expected 404 status and message,
        with a body that conforms to the strict GenericResponse schema.

        :param reviews_api: ReviewsAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param invalid_review_details: Parametrized test data containing an
                                       invalid review_id, expected status_code,
                                       and expected_message.
        """
        review_id = invalid_review_details['review_id']
        logger.info(f"Testing get_review_details with invalid review ID: {review_id}")
        allure.dynamic.title(f"Get details for invalid review ID: {review_id}")

        with allure.step(f"Send GET request for review ID {review_id}"):
            response = reviews_api.get_review_details(review_id)
            res_body = response.data

        with allure.step("Validate HTTP response metadata"):
            assert_get_metadata(response, invalid_review_details, 'review')

        with allure.step("Validate error message"):
            assert res_body['status_message'] == invalid_review_details['expected_message']
            assert res_body['success'] is False, "Request for an invalid review ID should report success=false"

        with allure.step("Validate response structure & schema (GenericResponse)"):
            load_schema('generic_schema').model_validate(res_body)