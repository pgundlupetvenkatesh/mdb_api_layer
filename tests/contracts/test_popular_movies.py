"""
Contract tests for popular Movies API using Pact.
"""

import allure
import pytest
from pact import match

from tests.schemas.models import PopularMoviesResponse, GenericResponse

@allure.epic("TMDB API")
@allure.feature("Contracts")
class TestPopularMovies:
    """
    Contract tests for Popular Movies API endpoints.

    The ``pact``, ``pact_movies_api`` and ``pact_address`` fixtures live in
    ``tests/contracts/conftest.py``; ``consumer_name`` names this consumer.
    """

    consumer_name = "test_popular_movies"

    @allure.story("Get Popular Movies Contract")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.contract
    def test_get_popular_movies(self, pact, pact_movies_api, pact_address):
        """
        Verify popular movies list response structure.

        Tests the GET /movie/popular endpoint with pagination.
        Verifies the response contains proper pagination and movie array.
        """
        allure.dynamic.title(f"Get Popular Movies")
        with allure.step("Define expected response structure with matchers"):
            expected_popular_response = {
                "page": match.int(1),
                "total_pages": match.int(500),
                "total_results": match.int(10000),
                "results": match.each_like({
                    "adult": match.like(False),
                    "backdrop_path": match.like("/path.jpg"),
                    "genre_ids": match.each_like(28),
                    "id": match.int(123),
                    "original_language": match.like("en"),
                    "original_title": match.like("Movie Title"),
                    "overview": match.like("Description..."),
                    "popularity": match.like(100.5),
                    "poster_path": match.like("/poster.jpg"),
                    "release_date": match.regex(
                        "2024-01-15",
                        regex=r"^\d{4}-\d{2}-\d{2}$"
                    ),
                    "title": match.like("Movie Title"),
                    "video": match.like(False),
                    "vote_average": match.like(7.5),
                    "vote_count": match.int(1000)
                })
            }

        with allure.step("Define expected Pact interaction for getting popular movies"):
            (
                pact
                .upon_receiving("a request for popular movies in page 1")
                .given("popular movies exist")
                .with_request("GET", "/3/movie/popular")
                .with_query_parameters({"page": "1"})
                .with_header('Authorization', match.like('Bearer token'), part='Request')
                .will_respond_with(200)
                .with_header('Content-Type', "application/json;charset=utf-8", part='Response')
                .with_body(expected_popular_response, content_type="application/json")
            )

        with allure.step("Start Pact mock server and send request to get popular movies"):
            host, port = pact_address
            with pact.serve(addr=host, port=port) as svr:
                 pact_movies_api.base_url = f"{svr.url}"
                 response = pact_movies_api.get_popular_movies({"page": 1})

        # Pact verified the *request* on exit; the response was mocked from our
        # matchers. Validate that mocked body against the same
        # PopularMoviesResponse contract the integration tests enforce.
        with allure.step("Validate response structure & schema (PopularMoviesResponse)"):
            assert response.status_code == 200
            PopularMoviesResponse.model_validate(response.data)

    @allure.story("Get Popular Invalid Movies Contract")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.contract
    def test_get_popular_movies_invalid_page(self, pact, pact_movies_api, pact_address):
        """
        Verify error response for invalid page parameter.

        Tests the GET /movie/popular endpoint with an invalid page number.
        Verifies the API returns a 400 Bad Request with appropriate error message.
        """
        allure.dynamic.title(f"Get Popular Movies for Invalid Page")
        with allure.step("Define expected response structure with matchers"):
            exp_error_res = {
                "success": match.like(False),
                "status_code": match.int(34),
                "status_message": match.like("The resource you requested could not be found.")
            }

        with allure.step("Define expected Pact interaction of getting popular movies for invalid page"):
            (
                pact
                .upon_receiving("a request for popular movies with invalid page")
                .given("invalid page parameter")
                .with_request("GET", "/3/movie/popular")
                .with_query_parameters({"page": "-1"})
                .with_header('Authorization', match.like('Bearer token'), part='Request')
                .will_respond_with(400)
                .with_header('Content-Type', 'application/json;charset=utf-8', part='Response')
                .with_body(exp_error_res, content_type="application/json")
            )

        with allure.step("Start Pact mock server and send request to get popular movies for invalid page"):
            host, port = pact_address
            with pact.serve(addr=host, port=port) as svr:
                pact_movies_api.base_url = f"{svr.url}"
                response = pact_movies_api.get_popular_movies({"page": -1})

        with allure.step("Validate response structure & schema (GenericResponse)"):
            assert response.status_code == 400
            assert response.data["success"] is False
            GenericResponse.model_validate(response.data)