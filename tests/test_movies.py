from xmlrpc.client import boolean

import pytest
from jsonschema import validate

from api.movies_api import MoviesAPI

class TestMoviesAPI:
    @pytest.fixture
    def movies_api(self):
        api = MoviesAPI()
        yield api  # Test runs here
        # api.close()  # Cleanup after test

    def test_get_movie_details(self, movies_api, load_schema):
        # movies_api creates MoviesAPI() instance
        # load_schema is a fixture from conftest.py

        movie_id = 550  # Example movie ID for "Fight Club"
        response = movies_api.get_movie_details(movie_id)
        res_body = response.data

        # Basic response validations
        assert response.request == 'GET', 'HTTP method is not GET'
        assert response.status_code == 200, 'returned status code is not 200'
        assert 'application/json' in response.headers['Content-Type'], 'response is not in JSON format'
        assert response.elapsed_seconds < 2, 'response time is too long'
        assert str(movie_id) in response.url, f"Response url should contain movie ID '{movie_id}'"
        assert res_body['id'] == movie_id, f"Movie ID should be {movie_id}"
        assert 'title' in res_body, "Response should contain 'title' field"
        assert res_body['title'] != "", "Response should contain 'title' field"

        # response structure validation
        assert isinstance(res_body['genres'], list), "Genres should be a list"
        if len(res_body['genres']) > 0:
            for idx, it in enumerate(res_body['genres']):
                assert 'id' in it, f"Genre at index {idx} should contain 'id' field"
                assert isinstance(it['id'], int), "Genres Id should be int"
                assert it['id'] > 0, "Genres Id should be positive"

                assert 'name' in it, f"Genre at index {idx} should contain 'name' field"
                assert isinstance(it['name'], str), "Genres name Id should be String"
                assert len(it['name']) > 0, "Genres name should not be empty"

        assert isinstance(res_body['id'], int), "Id Response should be int"
        assert res_body['id'] > 0, "Id should be positive"

        assert isinstance(res_body['adult'], bool), "Adult Response should be boolean"

        assert isinstance(res_body['origin_country'], list), "Origin Country Response should be a list"
        assert len(res_body['origin_country']) > 0, "Origin Country should not be empty"

        assert isinstance(res_body['original_language'], str), "Origin language Response should be string"
        assert len(res_body['original_language']) == 2, "Original language should be 2-char code"

        assert isinstance(res_body['title'], str), "Title Response should be string"
        assert len(res_body['title']) > 0, "Title should not be empty"

        assert isinstance(res_body['original_title'], str), "Original Title Response should be string"
        assert len(res_body['original_title']) > 0, "Original Title should not be empty"

        assert isinstance(res_body['production_companies'], list), "Production Companies Response should be a list"
        if len(res_body['production_companies']) > 0:
            for idx, it in enumerate(res_body['production_companies']):
                assert 'id' in it, f"Production Company at index {idx} should contain 'id' field"
                assert isinstance(it['id'], int), "Production Companies Id should be int"
                assert it['id'] > 0, "Id should be positive"

                assert 'logo_path' in it, f"Production Company at index {idx} should contain 'logo path' field"
                assert it['logo_path'] is None or isinstance(it['logo_path'],
                                  str), f"Production Companies at index {idx} Logo Path should be String"
                assert it['logo_path'] is None or it['logo_path'].endswith(
                    ('.png', '.jpg')), 'Production Companies Logo Path should be PNG'

                assert 'name' in it, f"Production Company at index {idx} should contain 'name' field"
                assert isinstance(it['name'], str), "Production Companies name should be String"
                assert len(it['name']) > 0, "Production Companies name should not be empty"

                assert 'origin_country' in it, f"Production Company at index {idx} should contain 'origin country' field"
                assert isinstance(it['origin_country'], str), "Production Companies Origin Country should be String"
                assert it['origin_country'] is None or len(it['origin_country']) > 0, "Origin Country should not be empty"

        # Validate response against JSON schema
        validate(instance=response.data, schema=load_schema('movie_schema'))

    def test_get_invalid_movie_details(self, movies_api, load_schema):
        movie_id = 0  # Invalid movie ID
        response = movies_api.get_movie_details(movie_id)
        res_body = response.data

        assert response.request == 'GET', 'HTTP method is not GET'
        assert response.status_code == 404, 'returned error status code is not 404'
        assert 'application/json' in response.headers['Content-Type'], 'response is not in JSON format'
        assert response.elapsed_seconds < 2, 'response time is too long'
        assert str(movie_id) in response.url, f"Response url should contain movie ID '{movie_id}'"
        assert res_body['status_message'] == "Invalid id: The pre-requisite id is invalid or not found."
