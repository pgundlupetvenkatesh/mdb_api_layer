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
                 Example ``response.data``::

                     {
                         "adult": false,
                         "id": 287,
                         "name": "Brad Pitt",
                         "gender": 2,
                         "known_for_department": "Acting",
                         "birthday": "1963-12-18",
                         "place_of_birth": "Shawnee, Oklahoma, USA",
                         "also_known_as": ["William Bradley Pitt"],
                         "biography": "William Bradley Pitt is an American actor...",
                         "imdb_id": "nm0000093",
                         "profile_path": "/cckcYc2v0yh5tnZTdZk6bnywnBv.png"
                     }
        """
        return self.get(f"{self._sub_path}/{person_id}")