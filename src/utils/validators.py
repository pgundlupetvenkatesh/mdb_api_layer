"""Utility functions for API testing."""
from typing import Dict, Any


def validate_movie_response(response_data: Dict[str, Any]) -> bool:
    """
    Validate that a movie response contains expected fields.
    
    Args:
        response_data: JSON response data from the API
        
    Returns:
        True if response contains expected fields, False otherwise
    """
    required_fields = ['Title', 'Year', 'imdbID', 'Type', 'Poster']
    return all(field in response_data for field in required_fields)


def validate_search_response(response_data: Dict[str, Any]) -> bool:
    """
    Validate that a search response contains expected fields.
    
    Args:
        response_data: JSON response data from the API
        
    Returns:
        True if response contains expected fields, False otherwise
    """
    if response_data.get('Response') == 'True':
        return 'Search' in response_data and 'totalResults' in response_data
    return 'Error' in response_data


def validate_error_response(response_data: Dict[str, Any]) -> bool:
    """
    Validate that an error response contains expected fields.
    
    Args:
        response_data: JSON response data from the API
        
    Returns:
        True if response is a valid error response, False otherwise
    """
    return (response_data.get('Response') == 'False' and 
            'Error' in response_data)
