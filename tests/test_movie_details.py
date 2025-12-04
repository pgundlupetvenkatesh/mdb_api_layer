"""Tests for OMDB API movie details functionality."""
import pytest
from src.utils import validate_error_response


@pytest.mark.details
@pytest.mark.smoke
class TestMovieDetails:
    """Test cases for getting movie details."""
    
    def test_get_movie_by_id_success(self, omdb_client, sample_movie_id):
        """Test getting movie details by IMDB ID."""
        response = omdb_client.get_by_id(sample_movie_id)
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'True'
        assert data['imdbID'] == sample_movie_id
        assert 'Title' in data
        assert 'Year' in data
        assert 'Plot' in data
        assert 'Director' in data
        assert 'Actors' in data
    
    def test_get_movie_by_id_with_full_plot(self, omdb_client, sample_movie_id):
        """Test getting movie with full plot."""
        response_short = omdb_client.get_by_id(sample_movie_id, plot='short')
        response_full = omdb_client.get_by_id(sample_movie_id, plot='full')
        
        assert response_short.status_code == 200
        assert response_full.status_code == 200
        
        data_short = response_short.json()
        data_full = response_full.json()
        
        # Full plot should be longer than short plot
        assert len(data_full['Plot']) >= len(data_short['Plot'])
    
    def test_get_movie_by_title_success(self, omdb_client, sample_movie_title):
        """Test getting movie details by title."""
        response = omdb_client.get_by_title(sample_movie_title)
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'True'
        assert data['Title'] == sample_movie_title
        assert 'imdbID' in data
        assert 'Year' in data
    
    def test_get_movie_by_title_with_year(self, omdb_client):
        """Test getting movie by title with year filter."""
        response = omdb_client.get_by_title('Batman', year='1989')
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'True'
        assert data['Year'] == '1989'
        assert data['Title'] == 'Batman'
    
    def test_get_movie_by_title_with_type(self, omdb_client):
        """Test getting movie by title with content type filter."""
        response = omdb_client.get_by_title('Breaking Bad', content_type='series')
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'True'
        assert data['Type'] == 'series'
    
    def test_get_movie_invalid_id(self, omdb_client):
        """Test getting movie with invalid IMDB ID returns error."""
        response = omdb_client.get_by_id('invalid123')
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'False'
        assert validate_error_response(data)
    
    def test_get_movie_nonexistent_title(self, omdb_client):
        """Test getting movie with non-existent title returns error."""
        response = omdb_client.get_by_title('xyzabc123nonexistentmovie')
        
        assert response.status_code == 200
        data = response.json()
        assert data['Response'] == 'False'
        assert validate_error_response(data)


@pytest.mark.details
@pytest.mark.regression
class TestMovieDetailsValidation:
    """Test validation of movie details responses."""
    
    def test_movie_response_contains_ratings(self, omdb_client, sample_movie_id):
        """Test that movie response contains ratings information."""
        response = omdb_client.get_by_id(sample_movie_id)
        
        assert response.status_code == 200
        data = response.json()
        assert 'Ratings' in data
        assert 'imdbRating' in data
        assert 'imdbVotes' in data
    
    def test_movie_response_contains_metadata(self, omdb_client, sample_movie_id):
        """Test that movie response contains all metadata fields."""
        response = omdb_client.get_by_id(sample_movie_id)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for essential metadata fields
        metadata_fields = [
            'Title', 'Year', 'Rated', 'Released', 'Runtime',
            'Genre', 'Director', 'Writer', 'Actors', 'Plot',
            'Language', 'Country', 'Awards', 'Poster', 'imdbID'
        ]
        
        for field in metadata_fields:
            assert field in data, f"Missing field: {field}"
    
    def test_movie_response_year_format(self, omdb_client, sample_movie_id):
        """Test that year is in expected format."""
        import re
        
        response = omdb_client.get_by_id(sample_movie_id)
        
        assert response.status_code == 200
        data = response.json()
        
        # Year should be a 4-digit string or a range (e.g., "2010-2015")
        # Pattern matches: "2020", "2010-2015", "2010–2015"
        year = data['Year']
        year_pattern = r'^\d{4}(-|–)?\d{0,4}$'
        assert re.match(year_pattern, year), f"Invalid year format: {year}"
    
    def test_movie_response_imdb_id_format(self, omdb_client, sample_movie_title):
        """Test that IMDB ID follows expected format."""
        response = omdb_client.get_by_title(sample_movie_title)
        
        assert response.status_code == 200
        data = response.json()
        
        # IMDB ID should start with 'tt' followed by digits
        imdb_id = data['imdbID']
        assert imdb_id.startswith('tt')
        assert imdb_id[2:].isdigit()
