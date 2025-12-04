"""OMDB API Client for making requests to the OMDB API."""
import requests
from typing import Dict, Optional, Any
from src.config import Config


class OMDBClient:
    """Client for interacting with the OMDB API."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the OMDB API client.
        
        Args:
            api_key: OMDB API key (defaults to Config.OMDB_API_KEY)
            base_url: Base URL for OMDB API (defaults to Config.OMDB_BASE_URL)
        """
        self.api_key = api_key or Config.OMDB_API_KEY
        self.base_url = base_url or Config.OMDB_BASE_URL
        
        if not self.api_key:
            raise ValueError("API key is required. Please provide it or set OMDB_API_KEY in environment.")
    
    def _make_request(self, params: Dict[str, Any]) -> requests.Response:
        """
        Make a request to the OMDB API.
        
        Args:
            params: Query parameters for the request
            
        Returns:
            Response object from the API
        """
        params['apikey'] = self.api_key
        response = requests.get(self.base_url, params=params)
        return response
    
    def search_movies(self, search_term: str, year: Optional[str] = None, 
                     page: int = 1, content_type: Optional[str] = None) -> requests.Response:
        """
        Search for movies by title.
        
        Args:
            search_term: Movie title to search for
            year: Year of release (optional)
            page: Page number for results (default: 1)
            content_type: Type of result (movie, series, episode) (optional)
            
        Returns:
            Response object containing search results
        """
        params = {
            's': search_term,
            'page': page
        }
        
        if year:
            params['y'] = year
        
        if content_type:
            params['type'] = content_type
        
        return self._make_request(params)
    
    def get_by_id(self, imdb_id: str, plot: str = 'short') -> requests.Response:
        """
        Get movie details by IMDB ID.
        
        Args:
            imdb_id: IMDB ID of the movie (e.g., tt1285016)
            plot: Plot length - 'short' or 'full' (default: short)
            
        Returns:
            Response object containing movie details
        """
        params = {
            'i': imdb_id,
            'plot': plot
        }
        
        return self._make_request(params)
    
    def get_by_title(self, title: str, year: Optional[str] = None, 
                    plot: str = 'short', content_type: Optional[str] = None) -> requests.Response:
        """
        Get movie details by title.
        
        Args:
            title: Movie title
            year: Year of release (optional)
            plot: Plot length - 'short' or 'full' (default: short)
            content_type: Type of result (movie, series, episode) (optional)
            
        Returns:
            Response object containing movie details
        """
        params = {
            't': title,
            'plot': plot
        }
        
        if year:
            params['y'] = year
        
        if content_type:
            params['type'] = content_type
        
        return self._make_request(params)
