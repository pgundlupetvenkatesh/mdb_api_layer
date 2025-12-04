"""Pytest fixtures for OMDB API tests."""
import pytest
import os
from src.api_client import OMDBClient
from src.config import Config


@pytest.fixture(scope='session')
def api_key():
    """Fixture to provide API key for tests."""
    # For testing purposes, allow using a test API key
    api_key = os.getenv('OMDB_API_KEY', '')
    if not api_key:
        pytest.skip("OMDB_API_KEY not set in environment variables")
    return api_key


@pytest.fixture(scope='session')
def omdb_client(api_key):
    """Fixture to provide an OMDB API client instance."""
    return OMDBClient(api_key=api_key)


@pytest.fixture(scope='session')
def sample_movie_id():
    """Fixture to provide a sample IMDB ID for testing."""
    return 'tt0111161'  # The Shawshank Redemption


@pytest.fixture(scope='session')
def sample_movie_title():
    """Fixture to provide a sample movie title for testing."""
    return 'The Matrix'


@pytest.fixture(scope='session')
def sample_search_term():
    """Fixture to provide a sample search term for testing."""
    return 'Batman'
