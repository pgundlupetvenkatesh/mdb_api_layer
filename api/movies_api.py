"""
Movies API client for The Movie Database (TMDB) endpoints.

This module provides a high-level interface for interacting with movie-related
TMDB API endpoints. It extends BaseAPI to inherit authentication, request
handling, and response parsing functionality.

Usage:
    api = MoviesAPI()
    response = api.get_movie_details(550)  # Get Fight Club details
    print(response.data['title'])
"""

from api.base_api import BaseAPI

class MoviesAPI(BaseAPI):
    """
    Client for TMDB Movies API endpoints.

    Provides methods for retrieving movie details, popular movies,
    top-rated movies, and alternative titles. All methods return
    a response object containing status code, headers, and parsed data.

    Attributes:
        _sub_path (str): Base path segment for movie endpoints.

    Example:
        api = MoviesAPI()
        movie = api.get_movie_details(550)
        popular = api.get_popular_movies({'page': 2})
    """

    _sub_path = "movie"

    def get_movie_details(self, movie_id):
        """
        Retrieve detailed information for a specific movie.

        :param movie_id: TMDB movie ID (e.g., 550 for Fight Club).
        :return: Response object with movie details including title,
                 genres, production companies, and release info.
        """
        return self.get(f"{self._sub_path}/{movie_id}")

    def get_popular_movies(self, query_params=None):
        """
        Retrieve a paginated list of currently popular movies.

        :param query_params: Optional dict of query parameters.
                             Defaults to page 1 if not specified.
        :return: Response object with paginated list of popular movies.
        """
        query_params ={ 'page': 1, **(query_params or {})}
        return self.get(f"{self._sub_path}/popular", params=query_params)

    def get_top_rated_movies(self, query_params=None):
        """
        Retrieve a paginated list of top-rated movies.

        :param query_params: Optional dict of query parameters.
                             Defaults to page 1 if not specified.
        :return: Response object with paginated list of top-rated movies.
        """
        query_params ={ 'page': 1 , **(query_params or {})}
        return self.get(f"{self._sub_path}/top_rated", params=query_params)

    def get_movie_by_alt_title(self, movie_id):
        """
        Retrieve alternative titles for a specific movie.

        Returns localized and regional title variations for the movie.

        :param movie_id: TMDB movie ID.
        :return: Response object with list of alternative titles
                 including country codes and title strings.
        """
        return self.get(f"{self._sub_path}/{movie_id}/alternative_titles")
