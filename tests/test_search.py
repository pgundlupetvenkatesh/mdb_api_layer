"""Tests for OMDB API search functionality."""
import pytest
from src.utils import validate_search_response, validate_error_response


@pytest.mark.search
@pytest.mark.smoke
class TestMovieSearch:
    """Test cases for movie search functionality."""
    
    def test_search_movies_success(self, omdb_client, sample_search_term):
        """Test searching for movies returns successful response."""
        response = omdb_client.search_movies(sample_search_term)
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'True'
        assert 'Search' in data
        assert 'totalResults' in data
        assert len(data['Search']) > 0
    
    def test_search_movies_with_year(self, omdb_client):
        """Test searching for movies with year filter."""
        response = omdb_client.search_movies('Batman', year='2008')
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'True'
        assert validate_search_response(data)
    
    def test_search_movies_with_type_filter(self, omdb_client, sample_search_term):
        """Test searching for movies with content type filter."""
        response = omdb_client.search_movies(sample_search_term, content_type='movie')
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'True'
        
        # Verify all results are movies
        for movie in data['Search']:
            assert movie['Type'] == 'movie'
    
    def test_search_movies_pagination(self, omdb_client, sample_search_term):
        """Test search pagination works correctly."""
        page1_response = omdb_client.search_movies(sample_search_term, page=1)
        page2_response = omdb_client.search_movies(sample_search_term, page=2)
        
        assert page1_response.status_code == 200
        assert page2_response.status_code == 200
        
        page1_data = page1_response.json()
        page2_data = page2_response.json()
        
        # Verify both pages have results
        assert page1_data['Response'] == 'True'
        assert page2_data['Response'] == 'True'
        
        # Verify pages are different
        if page2_data.get('Search'):
            page1_ids = [movie['imdbID'] for movie in page1_data['Search']]
            page2_ids = [movie['imdbID'] for movie in page2_data['Search']]
            assert page1_ids != page2_ids
    
    def test_search_no_results(self, omdb_client):
        """Test searching for non-existent movie returns appropriate response."""
        response = omdb_client.search_movies('xyzabc123nonexistent')
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'False'
        assert 'Error' in data
        assert validate_error_response(data)
    
    def test_search_empty_string(self, omdb_client):
        """Test searching with empty string returns error."""
        response = omdb_client.search_movies('')
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'False'
        assert validate_error_response(data)


@pytest.mark.search
@pytest.mark.regression
class TestSearchEdgeCases:
    """Test edge cases for search functionality."""
    
    def test_search_special_characters(self, omdb_client):
        """Test searching with special characters."""
        response = omdb_client.search_movies('Spider-Man')
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'True'
    
    def test_search_multiple_words(self, omdb_client):
        """Test searching with multiple words."""
        response = omdb_client.search_movies('The Dark Knight')
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'True'
        assert len(data['Search']) > 0
    
    def test_search_case_insensitive(self, omdb_client):
        """Test that search is case insensitive."""
        response_lower = omdb_client.search_movies('batman')
        response_upper = omdb_client.search_movies('BATMAN')
        
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        
        data_lower = response_lower.json()
        data_upper = response_upper.json()
        
        assert data_lower['Response'] == 'True'
        assert data_upper['Response'] == 'True'
