"""
Contract tests for popular Movies API using Pact.
"""

import pytest
import atexit
from pact import Consumer, Provider, Like, EachLike, Term

from api.movies_api import MoviesAPI

# Pact mock server config
PACT_MOCK_HOST = "localhost"
PACT_MOCK_PORT = 1234
PACT_DIR = "tests/pacts"


class TestPopularMovies:
    """
    Contract tests for Popular Movies API endpoints.
    """

    @pytest.fixture(scope="class")
    def pact(self):
        """
        Create a Pact instance for contract testing.

        This fixture:
        - Sets up a mock server that simulates the TMDB API
        - Captures request/response expectations
        - Generates contract files in PACT_DIR

        The consumer name identifies client service, and the provider name
        identifies the API being consumed (TMDB).
        """
        pact = Consumer("TestPopularMovie").has_pact_with(
            Provider("APIPvd"),
            host_name=PACT_MOCK_HOST,
            port=PACT_MOCK_PORT,
            pact_dir=PACT_DIR,
        )
        pact.start_service()

        # Register cleanup to run at exit
        atexit.register(pact.stop_service)

        yield pact

        # Verify all interactions were matched and write to pact file
        pact.stop_service()

    @pytest.fixture
    def pact_movies_api(self):
        """
        Create a MoviesAPI instance pointing to the Pact mock server.

        Override base URL to use the Pact mock server instead of the real TMDB API
        and test against expected responses.
        """
        api = MoviesAPI()
        api.base_url = f"http://{PACT_MOCK_HOST}:{PACT_MOCK_PORT}/3"
        return api

    @pytest.mark.contract
    def test_get_popular_movies(self, pact, pact_movies_api):
        """
        Verify popular movies list response structure.

        Tests the GET /movie/popular endpoint with pagination.
        Verifies the response contains proper pagination and movie array.
        """
        expected_popular_response = {
            "page": Like(1),
            "total_pages": Like(500),
            "total_results": Like(10000),
            "results": EachLike({
                "adult": Like(False),
                "backdrop_path": Like("/path.jpg"),
                "genre_ids": EachLike(28),
                "id": Like(123),
                "original_language": Like("en"),
                "original_title": Like("Movie Title"),
                "overview": Like("Description..."),
                "popularity": Like(100.5),
                "poster_path": Like("/poster.jpg"),
                "release_date": Term(
                    generate="2024-01-15",
                    matcher=r"^\d{4}-\d{2}-\d{2}$"
                ),
                "title": Like("Movie Title"),
                "video": Like(False),
                "vote_average": Like(7.5),
                "vote_count": Like(1000)
            })
        }

        (
            pact
            .given("popular movies exist")
            .upon_receiving("a request for popular movies page 1")
            .with_request(
                method="GET",
                path="/3/movie/popular",
                query={"page": "1"},
                headers={"Authorization": Like("Bearer token")}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json;charset=utf-8"},
                body=expected_popular_response
            )
        )

        with pact:
            response = pact_movies_api.get_popular_movies({"page": 1})

        assert response.status_code == 200
        assert "results" in response.data
        assert isinstance(response.data["results"], list)
        assert "page" in response.data

    @pytest.mark.contract
    def test_get_popular_movies_invalid_page(self, pact, pact_movies_api):
        """
        Verify error response for invalid page parameter.

        Tests the GET /movie/popular endpoint with an invalid page number.
        Verifies the API returns a 400 Bad Request with appropriate error message.
        """
        breakpoint()
        exp_error_res = {
            "success": Like(False),
            "status_code": Like(34),
            "status_message": Like("The resource you requested could not be found.")
        }

        (
            pact
            .given("invalid page parameter")
            .upon_receiving("a request for popular movies with invalid page")
            .with_request(
                method="GET",
                path="/3/movie/popular",
                query={"page": "-1"},
                headers={"Authorization": Like("Bearer token")}
            )
            .will_respond_with(
                status=400,
                headers={"Content-Type": "application/json;charset=utf-8"},
                body=exp_error_res
            )
        )

        with pact:
            response = pact_movies_api.get_popular_movies({"page": -1})

        assert response.status_code == 400
        assert "status_code" in response.data
        assert "status_message" in response.data