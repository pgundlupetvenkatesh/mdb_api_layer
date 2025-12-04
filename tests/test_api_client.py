"""Tests for OMDB API client initialization and error handling."""
import pytest
from src.api_client import OMDBClient
from src.config import Config


class TestClientInitialization:
    """Test cases for client initialization."""
    
    def test_client_initialization_with_api_key(self, api_key):
        """Test that client can be initialized with API key."""
        client = OMDBClient(api_key=api_key)
        assert client.api_key == api_key
        assert client.base_url == Config.OMDB_BASE_URL
    
    def test_client_initialization_with_custom_base_url(self, api_key):
        """Test that client can be initialized with custom base URL."""
        custom_url = "https://custom.omdbapi.com/"
        client = OMDBClient(api_key=api_key, base_url=custom_url)
        assert client.base_url == custom_url
    
    def test_client_initialization_without_api_key(self):
        """Test that client raises error when initialized without API key."""
        # Temporarily clear the environment variable
        import os
        original_key = os.environ.get('OMDB_API_KEY')
        if original_key:
            del os.environ['OMDB_API_KEY']
        
        try:
            with pytest.raises(ValueError, match="API key is required"):
                OMDBClient(api_key='')
        finally:
            # Restore original key
            if original_key:
                os.environ['OMDB_API_KEY'] = original_key


class TestAPIErrorHandling:
    """Test cases for API error handling."""
    
    def test_invalid_api_key_returns_error(self):
        """Test that invalid API key returns appropriate error."""
        client = OMDBClient(api_key='invalid_key_123')
        response = client.search_movies('Batman')
        
        assert response.status_code == 401 or response.status_code == 200
        data = response.json()
        
        # OMDB returns 200 with error message for invalid keys
        if response.status_code == 200:
            assert data['Response'] == 'False'
            assert 'Error' in data
    
    def test_request_timeout_handling(self, omdb_client):
        """Test that request handles timeout gracefully."""
        # This is a basic test - actual timeout testing would require mocking
        response = omdb_client.search_movies('Batman')
        assert response.status_code == 200


class TestResponseValidation:
    """Test cases for response validation."""
    
    def test_successful_response_structure(self, omdb_client, sample_search_term):
        """Test that successful response has expected structure."""
        response = omdb_client.search_movies(sample_search_term)
        
        assert response.status_code == 200
        data = response.json()
        
        # All responses should have 'Response' field
        assert 'Response' in data
        assert data['Response'] in ['True', 'False']
    
    def test_error_response_structure(self, omdb_client):
        """Test that error response has expected structure."""
        response = omdb_client.search_movies('')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['Response'] == 'False'
        assert 'Error' in data
        assert isinstance(data['Error'], str)
    
    def test_response_content_type(self, omdb_client, sample_search_term):
        """Test that response has correct content type."""
        response = omdb_client.search_movies(sample_search_term)
        
        assert response.status_code == 200
        assert 'application/json' in response.headers.get('Content-Type', '')
