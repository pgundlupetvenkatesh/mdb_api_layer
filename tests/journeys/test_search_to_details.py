"""
Journey integration test: search a movie, then open its details.

Unlike the single-endpoint suites, this test chains two live TMDB calls the
way a real user (and the perf ``JourneyUser``) does: it searches with
``GET /3/search/movie``, drills into the top result via ``GET /3/movie/{id}``,
and asserts the searched id resolves to the same movie. Each step is still
validated with the shared metadata + Pydantic-schema helpers, so this stays a
thin layer over the existing conventions; its added value is verifying the
contract *between* the two endpoints.

Seed queries are reused from the ``search_movies`` section of 'test_data.yaml'
(the same known-good set the search suite and perf ``SEARCH_QUERIES`` use),
keeping journey, functional and perf coverage single-sourced.

Usage:
    pytest tests/journeys/test_search_to_details.py -v
"""

import allure
import pytest

from loguru import logger
from tests.data.data_loader import load_test_data
from tests.helpers import *

SEARCH_DATA = load_test_data("test_data.yaml", "search_movies")
DETAILS_DATA = load_test_data("test_data.yaml", "get_movie_details")
"""Module-level test data loaded once at import time for parametrization."""

# Reuse the search suite's known-good valid cases, keeping only those that carry
# a text query — that's the field a movie id gets chained out of.
JOURNEY_CASES = [c for c in SEARCH_DATA['search_movies']['valid'] if 'query' in c['query_param']]
# Metadata template for the details step (200/OK + global defaults).
DETAILS_META = DETAILS_DATA['get_movie_details']['valid'][0]


@allure.epic("TMDB API")
@allure.feature("Journeys")
class TestSearchToDetails(FieldAssertions):
    """
    User-journey tests that chain the Search and Movies endpoints.

    Each test walks a realistic flow end to end, validating every step's
    response metadata and body schema and asserting that ids returned by one
    endpoint resolve correctly through the next.
    """

    @allure.story("Search then view movie details")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('search_case', JOURNEY_CASES)
    def test_search_then_get_details(self, search_api, movies_api, load_schema, search_case):
        """
        Search for a movie, then fetch the top result's full details.

        Mirrors the perf 'search-driven' journey: the id returned by
        ``search/movie`` is fed into ``movie/{id}`` and the response is
        asserted to describe the same movie, exercising the cross-endpoint
        contract that single-endpoint tests do not cover.

        :param search_api: SearchAPI client fixture from conftest.py.
        :param movies_api: MoviesAPI client fixture from conftest.py.
        :param load_schema: Schema loader fixture from conftest.py.
        :param search_case: Parametrized search case supplying the query
                            (reused from the search_movies valid data).
        """
        query = search_case['query_param']['query']
        allure.dynamic.title(f"Journey: search '{query}' -> movie details")
        logger.info(f"Running journey: search '{query}' then get movie details")

        with allure.step(f"Search movies for '{query}'"):
            search_res = search_api.search_movies(query_params=search_case['query_param'])
            assert_get_metadata(search_res, search_case, 'search/movie')
            load_schema('search_movies_schema').model_validate(search_res.data)

        with allure.step("Select the top movie id from the search results"):
            results = search_res.data['results']
            assert results, f"Search for '{query}' returned no results to drill into"
            movie_id = results[0]['id']

        with allure.step(f"Get details for movie {movie_id}"):
            details_res = movies_api.get_movie_details(movie_id)
            assert_get_metadata(details_res, DETAILS_META, movie_id)
            load_schema('movie_schema').model_validate(details_res.data)

        with allure.step("Validate the searched id resolves to the same movie"):
            assert details_res.data['id'] == movie_id, \
                f"Details id {details_res.data['id']} does not match searched id {movie_id}"
