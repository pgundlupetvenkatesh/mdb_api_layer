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
                 Example ``response.data``::

                     {
                         "id": 213,
                         "name": "Netflix",
                         "headquarters": "Los Gatos, California, USA",
                         "homepage": "https://www.netflix.com",
                         "logo_path": "/wwemzKWzjKYJFfCeiB57q3r4Bcm.png",
                         "origin_country": ""
                     }
        """
        return self.get(f"{self._sub_path}/{network_id}")