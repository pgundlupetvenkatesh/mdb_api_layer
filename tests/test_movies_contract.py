"""
Contract tests for the Movies API using Pact. Module demonstrates consumer-driven contract testing.

Contract Testing vs Integration Testing:
- Contract tests: Verify API structure/schema expectations (fast, no network)
- Integration tests: Verify actual API behavior (slower, requires live API)
- Consumer: Our test suite (expects certain response structure)
- Provider: TMDB API (serves the actual responses)
- Pact: JSON contract capturing request/response expectations
- Matchers: Define patterns (types, regex) instead of exact values
"""

import pytest
import atexit
from pact import Consumer, Provider, Like, EachLike, Term

from api.movies_api import MoviesAPI


# Pact mock server config
PACT_MOCK_HOST = "localhost"
PACT_MOCK_PORT = 1234
PACT_DIR = "tests/pacts"


class TestMoviesAPIContract:
    """
    Contract tests for MoviesAPI endpoints.

    Define what consumer (test client) expects from the TMDB provider.
    Pact generates a JSON contract that documents these expectations.

    Each test:
    1. Defines expected request/response using Pact DSL
    2. Runs against Pact mock server (not real API)
    3. Verifies response matches expectations
    4. Generates/updates the contract
    """

    # @pytest.fixture(scope="class")
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
        pact = Consumer("TMDBTestClient").has_pact_with(
            Provider("TMDBAPI"),
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

    # @pytest.fixture
    def pact_movies_api(self):
        """
        Create a MoviesAPI instance pointing to the Pact mock server.

        Override base URL to use the Pact mock server instead of the real TMDB API
        and test against expected responses.
        """
        api = MoviesAPI()
        # Override base URL to point to Pact mock server
        breakpoint()
        api.base_url = f"http://{PACT_MOCK_HOST}:{PACT_MOCK_PORT}/3"
        return api

    # @pytest.mark.contract
    def test_get_movie_details_contract(self, pact, pact_movies_api):
        """
        Contract test: Verify movie details response structure.

        This test defines our expectations for the GET /movie/{id} endpoint:
        - Expected request: GET /3/movie/550
        - Expected response: JSON with specific field types

        Using Like, EachLike, and Term allows to verify the response structure.
        """
        # Define the expected response structure using Pact matchers
        # Like() means "match by type, not exact value"
        expected_movie_response = {
            "adult": Like(False),                      # Boolean
            "id": Like(550),                           # Integer
            "title": Like("Fight Club"),               # String
            "original_title": Like("Fight Club"),      # String
            "original_language": Like("en"),           # String
            "overview": Like("A ticking-Loss..."),    # String (any text)
            "popularity": Like(61.416),                # Float
            "vote_average": Like(8.4),                 # Float
            "vote_count": Like(26280),                 # Integer
            "release_date": Term(                      # Date format: YYYY-MM-DD
                generate="1999-10-15",
                matcher=r"^\d{4}-\d{2}-\d{2}$"
            ),
            "runtime": Like(139),                      # Integer (minutes)
            "status": Like("Released"),                # String
            "tagline": Like("Mischief. Mayhem. Soap."), # String
            "genres": EachLike({                       # Array of genre objects
                "id": Like(18),
                "name": Like("Drama")
            }),
            "origin_country": EachLike("US"),          # Array of strings
            "production_companies": EachLike({         # Array of company objects
                "id": Like(508),
                "name": Like("Regency Enterprises"),
                "logo_path": Like("/7PzJdsLGlR7oW4J0J5Xcd0pHGRg.png"),
                "origin_country": Like("US")
            }),
        }

        # ARRANGE: Set up the expected interaction
        # "given" describes the provider state (precondition)
        # "upon_receiving" describes this specific interaction
        (
            pact
            .given("a movie with ID 550 exists")
            .upon_receiving("a request for movie details for movie ID 550")
            .with_request(
                method="GET",
                path="/3/movie/550",
                headers={"Authorization": Like("Bearer token")}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json;charset=utf-8"},
                body=expected_movie_response
            )
        )

        # Make the request through your API client and hit the Pact mock server
        with pact:
            response = pact_movies_api.get_movie_details(550)

        # ASSERT: Verify the response
        # Pact has already verified the structure matches expectations
        # You can add additional business logic assertions here
        assert response.status_code == 200
        assert "id" in response.data
        assert "title" in response.data
        assert isinstance(response.data["genres"], list)

    # @pytest.mark.contract
    def test_get_movie_details_not_found_contract(self, pact, pact_movies_api):
        """
        Contract test: Verify 404 error response for non-existent movie.

        This test ensures our client correctly handles error responses
        when requesting a movie that doesn't exist.

        Expected error response structure:
        - status_code: 34 (TMDB's error code for not found)
        - status_message: Error description
        - success: false
        """
        expected_error_response = {
            "success": Like(False),
            "status_code": Like(34),
            "status_message": Like("The resource you requested could not be found.")
        }

        (
            pact
            .given("movie with ID 99999999 does not exist")
            .upon_receiving("a request for non-existent movie ID 99999999")
            .with_request(
                method="GET",
                path="/3/movie/99999999",
                headers={"Authorization": Like("Bearer token")}
            )
            .will_respond_with(
                status=404,
                headers={"Content-Type": "application/json;charset=utf-8"},
                body=expected_error_response
            )
        )

        with pact:
            response = pact_movies_api.get_movie_details(99999999)

        assert response.status_code == 404
        assert response.data["success"] is False
        assert "status_message" in response.data

    # @pytest.mark.contract
    def test_get_popular_movies_contract(self, pact, pact_movies_api):
        """
        Contract test: Verify popular movies list response structure.

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


