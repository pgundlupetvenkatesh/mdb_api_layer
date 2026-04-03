"""
Contract tests for popular Movies API using Pact.
"""

import allure
import pytest
from pact import Pact, match

from api.movies_api import MoviesAPI

# Pact mock server config
PACT_MOCK_HOST = "localhost"
PACT_MOCK_PORT = 1234
PACT_DIR = "tests/pacts"

@allure.epic("TMDB API")
@allure.feature("Contracts")
class TestPopularMovies:
    """
    Contract tests for Popular Movies API endpoints.
    """

    @pytest.fixture
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
        pact = Pact('test_popular_movies', 'api_pvd')
        yield pact
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

    @allure.story("Get Popular Movies Contract")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.contract
    def test_get_popular_movies(self, pact, pact_movies_api):
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
                    "genre_ids": match.int(28),
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
            with pact.serve(addr=PACT_MOCK_HOST, port=PACT_MOCK_PORT) as svr:
                 pact_movies_api.base_url = f"{svr.url}"
                 response = pact_movies_api.get_popular_movies({"page": 1})

        with allure.step("Validate response content"):
            assert response.status_code == 200
            assert "results" in response.data
            assert isinstance(response.data["results"], list)
            assert "page" in response.data

    @allure.story("Get Popular Invalid Movies Contract")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.contract
    def test_get_popular_movies_invalid_page(self, pact, pact_movies_api):
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
            with pact.serve(addr=PACT_MOCK_HOST, port=PACT_MOCK_PORT) as svr:
                pact_movies_api.base_url = f"{svr.url}"
                response = pact_movies_api.get_popular_movies({"page": -1})

        with allure.step("Validate response content"):
            assert response.status_code == 400
            assert "status_code" in response.data
            assert "status_message" in response.data