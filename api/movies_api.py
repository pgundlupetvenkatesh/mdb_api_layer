"""
Movies API client for The Movie Database (TMDB) endpoints.

This module provides a high-level interface for interacting with movie-related
TMDB API endpoints. It extends BaseAPI to inherit authentication, request
handling, and response parsing functionality.

Usage:
    api = MoviesAPI()
    response = api.get_movie_details(550)  # Get Fight Club details
    logger.info(response.data['title'])
"""

from loguru import logger
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
                 Example ``response.data``::

                     {
                         "adult": false,
                         "id": 550,
                         "title": "Fight Club",
                         "original_title": "Fight Club",
                         "original_language": "en",
                         "release_date": "1999-10-15",
                         "origin_country": ["US"],
                         "genres": [{"id": 18, "name": "Drama"}],
                         "production_companies": [
                             {"id": 508, "logo_path": "/7cxRWzi4LsVm4Utfpr1hfARNurT.png",
                              "name": "Regency Enterprises", "origin_country": "US"}
                         ]
                     }
        """
        return self.get(f"{self._sub_path}/{movie_id}")

    def get_popular_movies(self, query_params=None):
        """
        Retrieve a paginated list of currently popular movies.

        :param query_params: Optional dict of query parameters.
                             Defaults to page 1 if not specified.
        :return: Response object with paginated list of popular movies.
                 Example ``response.data``::

                     {
                         "page": 1,
                         "results": [
                             {"id": 550, "title": "Fight Club", "original_language": "en",
                              "genre_ids": [18], "vote_average": 8.4, "vote_count": 26280,
                              "release_date": "1999-10-15"}
                         ],
                         "total_pages": 500,
                         "total_results": 10000
                     }
        """
        query_params ={ 'page': 1, **(query_params or {})}
        logger.debug(f"query_params: {query_params}")
        return self.get(f"{self._sub_path}/popular", params=query_params)

    def get_top_rated(self, query_params=None):
        """
        Retrieve a paginated list of top-rated movies.

        :param query_params: Optional dict of query parameters.
                             Defaults to page 1 if not specified.
        :return: Response object with paginated list of top-rated movies.
                 Example ``response.data``::

                     {
                         "page": 1,
                         "results": [
                             {"id": 278, "title": "The Shawshank Redemption",
                              "original_language": "en", "vote_average": 8.7,
                              "vote_count": 27000, "release_date": "1994-09-23"}
                         ],
                         "total_pages": 500,
                         "total_results": 10000
                     }
        """
        query_params ={ 'page': 1 , **(query_params or {})}
        return self.get(f"{self._sub_path}/top_rated", params=query_params)

    def get_movie_reviews(self, movie_id, query_params=None):
        """
        Retrieve user reviews for a specific movie.

        :param movie_id: TMDB movie ID.
        :param query_params: Optional dict of query parameters (e.g., page).
        :return: Response object with a paginated list of user reviews.
                 Example ``response.data``::

                     {
                         "id": 550,
                         "page": 1,
                         "results": [
                             {"id": "5b1c13b9c3a36848f2026384", "author": "Cat Ellington",
                              "author_details": {"name": "Cat Ellington",
                                                 "username": "CatEllington",
                                                 "avatar_path": null, "rating": 8.0},
                              "content": "The film that launched...",
                              "created_at": "2018-06-09T18:15:37.023Z",
                              "updated_at": "2021-06-23T15:58:09.043Z",
                              "url": "https://www.themoviedb.org/review/5b1c13b9c3a36848f2026384"}
                         ],
                         "total_pages": 1,
                         "total_results": 8
                     }
        """
        logger.debug(f"query_params: {query_params}")
        return self.get(f"{self._sub_path}/{movie_id}/reviews", params=query_params)

    def get_alt_title(self, movie_id):
        """
        Retrieve alternative titles for a specific movie.

        Returns localized and regional title variations for the movie.

        :param movie_id: TMDB movie ID.
        :return: Response object with list of alternative titles
                 including country codes and title strings.
                 Example ``response.data``::

                     {
                         "id": 550,
                         "titles": [
                             {"iso_3166_1": "BR", "title": "Clube da Luta", "type": ""},
                             {"iso_3166_1": "PL", "title": "Podziemny krąg", "type": ""}
                         ]
                     }
        """
        return self.get(f"{self._sub_path}/{movie_id}/alternative_titles")

    def  add_rating(self, movie_id, rating, query_params=None):
        """
        Add a user rating for a specific movie.

        :param movie_id: TMDB movie ID.
        :param rating: User rating value (0.5 to 10.0).
        :param query_params: Optional dict of query parameters, such as session_id for authentication.
        :return: Response object with status of the rating submission.
                 Example ``response.data``::

                     {"success": true, "status_code": 1, "status_message": "Success."}
        """
        payload = {'value': rating}
        return self.post(f"{self._sub_path}/{movie_id}/rating", params=query_params, json=payload)

    def  delete_rating(self, movie_id, query_params=None):
        """
        Delete a user rating for a specific movie.

        :param movie_id: TMDB movie ID.
        :param query_params: Optional dict of query parameters, such as session_id for authentication.
        :return: Response object with status of the rating deletion.
                 Example ``response.data``::

                     {"success": true, "status_code": 13,
                      "status_message": "The item/record was deleted successfully."}
        """
        return self.delete(f"{self._sub_path}/{movie_id}/rating", params=query_params)