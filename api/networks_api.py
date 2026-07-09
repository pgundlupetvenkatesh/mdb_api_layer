from api.base_api import BaseAPI

class NetworksAPI(BaseAPI):
    """
    Client for TMDB Networks API endpoints.

    Provides methods for retrieving TV network details. All methods return
    a response object containing status code, headers, and parsed data.

    Attributes:
        _sub_path (str): Base path segment for network endpoints.
    """

    _sub_path = "network"

    def get_network_details(self, network_id):
        """
        Retrieve detailed information for a specific TV network.

        :param network_id: TMDB network ID (e.g., 213 for Netflix).
        :return: Response object with network details including name,
                 headquarters, homepage, logo path, and origin country.
        """
        return self.get(f"{self._sub_path}/{network_id}")