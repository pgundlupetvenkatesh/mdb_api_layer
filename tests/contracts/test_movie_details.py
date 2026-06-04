"""
Contract tests for the Movies Details API. Module demonstrates consumer-driven contract (CDC) testing.
"""

import allure
import pytest
from pact import match

from tests.schemas.models import MovieDetails, GenericResponse

@allure.epic("TMDB API")
@allure.feature("Contracts")
class TestMovieDetails:
    """
    Contract tests for Movies Details API endpoint. Define what consumer (test client) expects from the provider,
    in our case Devs/PO.

    The ``pact``, ``pact_movies_api`` and ``pact_address`` fixtures live in
    ``tests/contracts/conftest.py``; ``consumer_name`` names this consumer.
    """

    consumer_name = "test_movie_details"

    @allure.story("Get Movie Details Contract")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.contract
    def test_get_movie_details(self, pact, pact_movies_api, pact_address):
        """
        Verify movie details response structure. Defines expectations for the GET /movie/{id} endpoint.
        Using matchers to allows flexible type-based matching rather than exact value comparison.
        match.like() = "match by type, not exact value"
        """
        allure.dynamic.title(f"Get Movie Details")
        allure.dynamic.description(f"Verify movie details response structure for movie ID 550 (Fight Club). Using matchers to allow flexible type-based matching.")
        with allure.step("Define expected response structure with matchers"):
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
        with allure.step("Define expected Pact interaction for getting movie details"):
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
        with allure.step("Start Pact mock server and send request to get movie details"):
            host, port = pact_address
            with pact.serve(addr=host, port=port) as srv:
                pact_movies_api.base_url = f"{srv.url}"
                response = pact_movies_api.get_movie_details(550)

        # Pact verified the *request* on exit; the response was mocked from our
        # matchers. Validate that mocked body against the same MovieDetails
        # contract the integration tests enforce (single source of truth).
        with allure.step("Validate response structure & schema (MovieDetails)"):
            assert response.status_code == 200
            MovieDetails.model_validate(response.data)

    @allure.story("Get Invalid Movie Details Contract")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.contract
    def test_get_invalid_movie_details(self, pact, pact_movies_api, pact_address):
        """
        Verify 404 error response for non-existent movie to test the client correctly handles error responses
        when requesting invalid movie ID.
        """
        allure.dynamic.title(f"Get Invalid Movie Details")
        allure.dynamic.description(f"Verify 404 error response structure for non-existent movie ID 99999999. Using matchers to allow flexible type-based matching.")
        with allure.step("Define expected response structure with matchers"):
            expected_error_response = {
                "success": match.like(False),
                "status_code": match.int(34),
                "status_message": match.like("The resource you requested could not be found."),
            }

        with allure.step("Define expected Pact interaction for getting invalid movie details"):
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

        with allure.step("Start Pact mock server and send request to get invalid movie details"):
            host, port = pact_address
            with pact.serve(addr=host, port=port) as srv:
                pact_movies_api.base_url = f"{srv.url}"
                response = pact_movies_api.get_movie_details(99999999)

        with allure.step("Validate response structure & schema (GenericResponse)"):
            assert response.status_code == 404
            assert response.data["success"] is False
            GenericResponse.model_validate(response.data)