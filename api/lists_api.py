from loguru import logger
from config.config import Config
from api.base_api import BaseAPI

class ListsAPI(BaseAPI):
    """
    Client for TMDB Lists API endpoints.

    Provides methods for creating, updating, deleting lists, and managing list items.
    All methods return a response object containing status code, headers, and parsed data.

    Attributes:
        _sub_path (str): Base path segment for list endpoints.
    Example:
        api = ListsAPI()
        new_list = api.create_list(name="My Favorite Movies", description="A list of my
        favorite movies", language="en")
    """
    _sub_path = "list"

    def __init__(self):
        """
        Initialize the ListsAPI client.

        Calls the parent :class:`BaseAPI` constructor, then overrides:
        - ``api_version`` to ``'4'`` (Lists API uses TMDB API v4).
        - ``Authorization`` header to use the user access token instead of the default auth token.

        Other headers (``Content-Type``, ``Connection``) are inherited from :class:`BaseAPI`.
        """
        super().__init__()
        self.api_version = '4'  # Override API version for lists endpoints
        self.headers['Authorization'] = f'Bearer {Config.USER_ACCESS_TOKEN}'

    def update_list(self, list_id, payload):
        """
        Update an existing list's metadata details.

        :param list_id: TMDB list ID to update.
        :param payload: Dict containing fields to update (e.g., name, description).
        :return: Response object with updated list details.
        """
        logger.info(f"Body payload: {payload}")
        return self.put(f"{self._sub_path}/{list_id}", data=payload)