from loguru import logger
from api.base_api import BaseAPI

class PeopleAPI(BaseAPI):
    """
    Client for TMDB People API endpoints.

    Provides methods for retrieving person details, popular people,
    and top-rated people. All methods return a response object containing
    status code, headers, and parsed data.

    Attributes:
        _sub_path (str): Base path segment for people endpoints.
    """

    _sub_path = "person"

    def get_person_details(self, person_id):
        """
        Retrieve detailed information for a specific person.

        :param person_id: TMDB person ID (e.g., 287 for Brad Pitt).
        :return: Response object with person details including name,
                 biography, known for movies, and birth info.
        """
        return self.get(f"{self._sub_path}/{person_id}")