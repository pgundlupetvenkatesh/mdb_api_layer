"""
Discover API client for The Movie Database (TMDB) endpoints.

This module provides a high-level interface for interacting with discover-related
TMDB API endpoints. It extends BaseAPI to inherit authentication, request
handling, and response parsing functionality.

Usage:
    api = DiscoverAPI()
    response = api.discover_movies({'with_genres': '28'})
    logger.info(response.data['total_results'])
"""

from loguru import logger
from api.base_api import BaseAPI

class DiscoverAPI(BaseAPI):
    """
    Client for TMDB Discover API endpoints.

    Provides methods for discovering movies by filtering and sorting across
    a wide range of attributes (genres, release dates, ratings, language,
    etc.). All methods return a response object containing status code,
    headers, and parsed data.

    Attributes:
        _sub_path (str): Base path segment for discover endpoints.

    Example:
        api = DiscoverAPI()
        results = api.discover_movies({'with_genres': '28', 'sort_by': 'popularity.desc'})
    """

    _sub_path = "discover"

    def discover_movies(self, query_params=None):
        """
        Discover movies by filter and sort criteria.

        Supported query parameters include: sort_by, include_adult,
        include_video, language, page, region, year, primary_release_year,
        with_genres, with_original_language, vote_average.gte and
        vote_count.gte (among others documented by TMDB).

        :param query_params: Optional dict of query parameters.
                             Defaults to page 1 if not specified.
        :return: Response object with paginated list of matching movies.
                 Example ``response.data``::

                     {
                         "page": 1,
                         "results": [
                             {"id": 27205, "title": "Inception", "original_language": "en",
                              "genre_ids": [28, 878, 12], "vote_average": 8.4,
                              "release_date": "2010-07-15"}
                         ],
                         "total_pages": 500,
                         "total_results": 10000
                     }
        """
        query_params = {'page': 1, **(query_params or {})}
        logger.debug(f"query_params: {query_params}")
        return self.get(f"{self._sub_path}/movie", params=query_params)