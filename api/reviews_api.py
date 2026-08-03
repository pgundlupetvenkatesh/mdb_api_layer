"""
Reviews API client for The Movie Database (TMDB) endpoints.

This module provides a high-level interface for interacting with review-related
TMDB API endpoints. It extends BaseAPI to inherit authentication, request
handling, and response parsing functionality.

Usage:
    api = ReviewsAPI()
    response = api.get_review_details("5b1c13b9c3a36848f2026384")
    logger.info(response.data['author'])
"""

from loguru import logger
from api.base_api import BaseAPI

class ReviewsAPI(BaseAPI):
    """
    Client for TMDB Reviews API endpoints.

    Provides methods for retrieving a single user review by its id. All methods
    return a response object containing status code, headers, and parsed data.

    Attributes:
        _sub_path (str): Base path segment for review endpoints.

    Example:
        api = ReviewsAPI()
        review = api.get_review_details("5b1c13b9c3a36848f2026384")
    """

    _sub_path = "review"

    def get_review_details(self, review_id):
        """
        Retrieve detailed information for a specific review.

        :param review_id: TMDB review ID (a 24-character hex string).
        :return: Response object with review details including author,
                 content, media reference, and timestamps.
                 Example ``response.data``::

                     {
                         "id": "5b1c13b9c3a36848f2026384",
                         "author": "Cat Ellington",
                         "author_details": {
                             "name": "Cat Ellington", "username": "CatEllington",
                             "avatar_path": null, "rating": 8.0
                         },
                         "content": "The film that launched a thousand fight clubs...",
                         "created_at": "2018-06-09T18:15:37.023Z",
                         "iso_639_1": "en",
                         "media_id": 550,
                         "media_title": "Fight Club",
                         "media_type": "movie",
                         "updated_at": "2021-06-23T15:58:09.043Z",
                         "url": "https://www.themoviedb.org/review/5b1c13b9c3a36848f2026384"
                     }
        """
        logger.info(f"Fetching review details for review_id: {review_id}")
        return self.get(f"{self._sub_path}/{review_id}")