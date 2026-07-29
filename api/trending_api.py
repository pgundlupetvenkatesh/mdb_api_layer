"""
Trending API client for The Movie Database (TMDB) endpoints.

This module provides a high-level interface for interacting with trending-related
TMDB API endpoints. It extends BaseAPI to inherit authentication, request
handling, and response parsing functionality.

Usage:
    api = TrendingAPI()
    response = api.get_trending_movies('day')
    logger.info(response.data['total_results'])
"""

from loguru import logger
from api.base_api import BaseAPI

class TrendingAPI(BaseAPI):
    """
    Client for TMDB Trending API endpoints.

    Provides methods for retrieving the movies trending over a given time
    window. All methods return a response object containing status code,
    headers, and parsed data.

    Attributes:
        _sub_path (str): Base path segment for trending endpoints.

    Example:
        api = TrendingAPI()
        trending = api.get_trending_movies('week')
    """

    _sub_path = "trending"

    def get_trending_movies(self, time_window, query_params=None):
        """
        Retrieve the movies trending over a given time window.

        :param time_window: Trending window, either ``'day'`` or ``'week'``.
        :param query_params: Optional dict of query parameters.
                             Defaults to page 1 if not specified.
        :return: Response object with paginated list of trending movies.
        """
        query_params = {'page': 1, **(query_params or {})}
        logger.debug(f"query_params: {query_params}")
        return self.get(f"{self._sub_path}/movie/{time_window}", params=query_params)
