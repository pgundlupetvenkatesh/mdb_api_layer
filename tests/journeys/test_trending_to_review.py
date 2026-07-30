"""
Journey integration test: browse trending movies, open a movie's reviews, then
drill into a single review's full details.

This chains three live TMDB calls the way a real user does when reading reviews:
it lists trending movies with ``GET /3/trending/movie/{time_window}``, opens the
first trending movie that has reviews via ``GET /3/movie/{id}/reviews``, then
fetches that review's full record with ``GET /3/review/{review_id}`` — asserting
the ``movie -> review -> review-details`` triangle closes (the review resolves to
the same id, and its ``media_id`` points back to the trending movie we started
from). Each step is still validated with the shared metadata + Pydantic-schema
helpers, so this stays a thin layer over the existing conventions; its added value
is verifying the contract *between* the three endpoints — and it is the only test
that validates the ``movie/{id}/reviews`` list body against a schema.

Most movies have no reviews, so rather than the random-movie walk that
``pick_random_review_id`` does, this seeds from trending movies — current and
famous, so they almost always have reviews — and iterates the trending page until
one does. If none do (rare), the test skips: that's a data condition, not a code
failure.

Metadata templates are reused from the ``trending_movies`` and
``get_review_details`` sections of 'test_data.yaml'; no new data block is needed.

Usage:
    pytest tests/journeys/test_trending_to_review.py -v
"""

import allure
import pytest

from loguru import logger
from tests.data.data_loader import load_test_data
from tests.helpers import *

TREND_DATA = load_test_data("test_data.yaml", "trending_movies")
REVIEW_DATA = load_test_data("test_data.yaml", "get_review_details")
"""Module-level test data loaded once at import time for parametrization."""

# Metadata template for the trending step and the reviews-list step (both 200/OK
# GETs under the default elapsed budget); assert_get_metadata ignores the extra
# time_window/exp_page keys.
TREND_META = TREND_DATA['trending_movies']['valid'][0]
# Metadata template for the review-details step (200/OK).
REVIEW_META = REVIEW_DATA['get_review_details']['valid'][0]

# Both trending windows give the seed page two chances to surface a reviewed movie.
TIME_WINDOWS = ['day', 'week']


@allure.epic("TMDB API")
@allure.feature("Journeys")
class TestTrendingToReview(FieldAssertions):
    """
    User-journey tests that chain the Trending, Movies and Reviews endpoints.

    Each test walks a realistic review-reading flow end to end, validating every
    step's response metadata and body schema and asserting that ids returned by
    one endpoint resolve correctly through the next.
    """

    @allure.story("Browse trending then read a movie review's details")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('time_window', TIME_WINDOWS)
    def test_trending_movie_review_details(self, trending_api, movies_api, reviews_api,
                                           load_schema, time_window):
        """
        List trending movies, open the first one that has reviews, then fetch that
        review's full details.

        A review id harvested from ``movie/{id}/reviews`` is fed into
        ``review/{review_id}``, and the review-details ``media_id`` is asserted to
        point back to the trending movie the review was found on.

        :param trending_api: TrendingAPI client fixture.
        :param movies_api: MoviesAPI client fixture.
        :param reviews_api: ReviewsAPI client fixture.
        :param load_schema: Schema loader fixture.
        :param time_window: Trending window path segment ('day' or 'week').
        """
        allure.dynamic.title(f"Journey: trending '{time_window}' -> movie reviews -> review details")
        logger.info(f"Running journey: trending '{time_window}' then drill into a review")

        with allure.step(f"List trending movies for '{time_window}'"):
            trending_res = trending_api.get_trending_movies(time_window)
            assert_get_metadata(trending_res, TREND_META, f'trending/movie/{time_window}')
            load_schema('trending_movies_schema').model_validate(trending_res.data)
            trending_movies = trending_res.data['results']
            assert trending_movies, f"Trending ({time_window}) returned no movies to drill into"

        with allure.step("Find the first trending movie that has reviews"):
            reviews_res = None
            movie_id = None
            for movie in trending_movies:
                candidate_id = movie['id']
                candidate_res = movies_api.get_movie_reviews(candidate_id)
                if candidate_res.data.get('results'):
                    reviews_res, movie_id = candidate_res, candidate_id
                    logger.info(f"Movie {movie_id} has reviews; drilling in")
                    break
            if reviews_res is None:
                pytest.skip(f"No trending ({time_window}) movie had reviews")

            assert_get_metadata(reviews_res, TREND_META, f'movie/{movie_id}/reviews')
            load_schema('movie_reviews_schema').model_validate(reviews_res.data)

        with allure.step("Select the top review id from the movie's reviews"):
            review_id = reviews_res.data['results'][0]['id']

        with allure.step(f"Get details for review {review_id}"):
            details_res = reviews_api.get_review_details(review_id)
            assert_get_metadata(details_res, REVIEW_META, review_id)
            load_schema('review_details_schema').model_validate(details_res.data)

        with allure.step("Validate the review resolves and points back to the movie"):
            assert details_res.data['id'] == review_id, \
                f"Details id {details_res.data['id']} does not match review id {review_id}"
            assert details_res.data['media_id'] == movie_id, \
                f"Review media_id {details_res.data['media_id']} does not match trending movie id {movie_id}"