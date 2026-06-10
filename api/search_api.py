"""
Search API client for The Movie Database (TMDB) endpoints.

This module provides a high-level interface for interacting with search-related
TMDB API endpoints. It extends BaseAPI to inherit authentication, request
handling, and response parsing functionality.

Usage:
    api = SearchAPI()
    response = api.search_movies({'query': 'Batman'})
    logger.info(response.data['total_results'])
"""

from loguru import logger
from api.base_api import BaseAPI

class SearchAPI(BaseAPI):
    """
    Client for TMDB Search API endpoints.

    Provides methods for searching movies by their original, translated
    and alternative titles. All methods return a response object containing
    status code, headers, and parsed data.

    Attributes:
        _sub_path (str): Base path segment for search endpoints.

    Example:
        api = SearchAPI()
        results = api.search_movies({'query': 'Batman', 'year': '1989'})
    """

    _sub_path = "search"

    def search_movies(self, query_params=None):
        """
        Search for movies by title with optional filters.

        Supported query parameters: query, include_adult, language,
        primary_release_year, page, region, year.

        :param query_params: Optional dict of query parameters.
                             Defaults to page 1 if not specified.
        :return: Response object with paginated list of matching movies.
        """
        query_params = {'page': 1, **(query_params or {})}
        logger.debug(f"query_params: {query_params}")
        return self.get(f"{self._sub_path}/movie", params=query_params)
