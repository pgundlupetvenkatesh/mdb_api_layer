"""
Contract tests for the Movies Details API. Module demonstrates consumer-driven contract (CDC) testing.
"""

import pytest
from pact import Pact, match

from api.movies_api import MoviesAPI

# Pact mock server config
PACT_MOCK_HOST = "localhost"
PACT_MOCK_PORT = 1234
PACT_DIR = "tests/pacts"

class TestMovieDetails:
    """
    Contract tests for Movies Details API endpoint. Define what consumer (test client) expects from the provider,
    in our case Devs/PO.
    """

    @pytest.fixture
    def pact(self):
        """
        Create a Pact instance for contract testing. Fixture creates a fresh Pact per test because once pact.serve()
        runs and the context manager exits, the Pact handle is finalized and no new interactions can be added to it.
        The consumer name identifies client service, and the provider name identifies the API being consumed (TMDB).

        Yields:
            Pact: Configured Pact instance ready for interaction definition.
        """
        pact = Pact("test_movie_details", "api_pvd")
        yield pact

        # Write/merge the contract file after each test
        pact.write_file(directory=PACT_DIR)

    @pytest.fixture
    def pact_movies_api(self):
        """
        Create a MoviesAPI instance pointing to the Pact mock server.

        Override base URL to use the Pact mock server instead of the real TMDB API
        and test against expected responses.
        """
        api = MoviesAPI()
        return api

    @pytest.mark.contract
    def test_get_movie_details(self, pact, pact_movies_api):
        """
        Verify movie details response structure. Defines expectations for the GET /movie/{id} endpoint.
        Using matchers to allows flexible type-based matching rather than exact value comparison.
        match.like() = "match by type, not exact value"
        """
        exp_movie_details_response = {
            "adult": match.like(False),                          # Boolean
            "id": match.int(550),                                # Integer
            "title": match.like("Fight Club"),                   # String
            "original_title": match.like("Fight Club"),          # String
            "original_language": match.like("en"),               # String
            "overview": match.like("A ticking-Loss..."),         # String (any text)
            "popularity": match.like(61.416),                    # Float
            "vote_average": match.like(8.4),                     # Float
            "vote_count": match.int(26280),                      # Integer
            "release_date": match.regex(                         # Date format: YYYY-MM-DD
                "1999-10-15",
                regex=r"^\d{4}-\d{2}-\d{2}$",
            ),
            "runtime": match.int(139),                           # Integer (minutes)
            "status": match.like("Released"),                    # String
            "tagline": match.like("Mischief. Mayhem. Soap."),    # String
            "genres": match.each_like({                          # Array of genre objects
                "id": match.int(18),
                "name": match.like("Drama"),
            }),
            "origin_country": match.each_like("US"),             # Array of strings
            "production_companies": match.each_like({            # Array of company objects
                "id": match.int(508),
                "name": match.like("Regency Enterprises"),
                "logo_path": match.like("/7PzJdsLGlR7oW4J0J5Xcd0pHGRg.png"),
                "origin_country": match.like("US"),
            }),
        }

        '''
        Setting up the expected interaction.
        "given" describes the provider state (precondition)
        "upon_receiving" describes this specific interaction
        '''
        (
            pact
            .upon_receiving("a request for movie details for movie ID 550")
            .given("a movie with ID 550 exists")
            .with_request("GET", "/3/movie/550")
            .with_header("Authorization", match.like("Bearer token"), part="Request")
            .will_respond_with(200)
            .with_header("Content-Type", "application/json;charset=utf-8", part="Response")
            .with_body(exp_movie_details_response, content_type="application/json")
        )

        # Start mock server, make request and verify on exit
        with pact.serve(addr=PACT_MOCK_HOST, port=PACT_MOCK_PORT) as srv:
            pact_movies_api.base_url = f"{srv.url}/3"
            response = pact_movies_api.get_movie_details(550)

        # Response structure has already been verified on context exit.
        assert response.status_code == 200
        assert "id" in response.data
        assert "title" in response.data
        assert isinstance(response.data["genres"], list)

    @pytest.mark.contract
    def test_get_invalid_movie_details(self, pact, pact_movies_api):
        """
        Verify 404 error response for non-existent movie to test the client correctly handles error responses
        when requesting invalid movie ID.
        """
        expected_error_response = {
            "success": match.like(False),
            "status_code": match.int(34),
            "status_message": match.like("The resource you requested could not be found."),
        }

        (
            pact
            .upon_receiving("a request for non-existent movie ID 99999999")
            .given("movie with ID 99999999 does not exist")
            .with_request("GET", "/3/movie/99999999")
            .with_header("Authorization", match.like("Bearer token"), part="Request")
            .will_respond_with(404)
            .with_header("Content-Type", "application/json;charset=utf-8", part="Response")
            .with_body(expected_error_response, content_type="application/json")
        )

        with pact.serve(addr=PACT_MOCK_HOST, port=PACT_MOCK_PORT) as srv:
            pact_movies_api.base_url = f"{srv.url}/3"
            response = pact_movies_api.get_movie_details(99999999)

        assert response.status_code == 404
        assert response.data["success"] is False
        assert "status_message" in response.data