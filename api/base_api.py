"""
Base API Module
===============

This module provides the foundation for all API interactions with the Movie Database.

.. module:: api.base_api
   :synopsis: Base API client with common HTTP methods.

"""

import requests
from dataclasses import dataclass
from typing import Any, Optional

from config.config import Config


@dataclass
class APIResponse:
    data: dict
    status_code: int
    url: str
    headers: Any
    cookies: Any
    encoding: str
    elapsed_seconds: float = 0.0
    reason: str = ""
    request: str = ""
    request_params: Optional[dict] = None
    request_payload: Optional[dict] = None

class BaseAPI:
    """
    Base API client providing common HTTP methods.

    This class handles authentication, session management, and HTTP operations
    for interacting with the Movie Database API.

    :ivar base_url: The base URL for API requests.
    :ivar headers: Default headers including authentication.
    :ivar session: Persistent requests session.
    """

    def __init__(self):
        """
        Initialize the BaseAPI with configuration settings.
        """
        self.base_url = Config.BASE_URL
        self.api_version = Config.API_VERSION
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {Config.AUTH_TOKEN}',
            'Connection': 'keep-alive'
        }
        self.session = requests.Session()

    def get(self, endpoint, params=None):
        """
        Perform a GET request to the specified endpoint.

        :param endpoint: API endpoint path.
        :type endpoint: str
        :param params: Optional query parameters.
        :type params: dict, optional
        :returns: Parsed JSON response.
        :rtype: dict
        """
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        response = self.session.get(url, headers=self.headers, params=params, timeout=Config.TIMEOUT)

        return APIResponse(
            data=response.json(),
            status_code=response.status_code,
            url=response.url,
            headers=response.headers,
            cookies=response.cookies,
            encoding=response.encoding,
            elapsed_seconds=response.elapsed.total_seconds(),
            reason=response.reason,
            request=str(response.request.method),
            request_params=params
        )


    def post(self, endpoint, json=None, params=None):
        """
        Perform a POST request to the specified endpoint.

        :param endpoint: API endpoint path.
        :type endpoint: str
        :param json: JSON payload to send in the request body.
        :type json: dict, optional
        :param params: Optional query parameters.
        :type params: dict, optional
        :returns: API response with data, status code, and metadata.
        :rtype: APIResponse
        """
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        response = self.session.post(url, params=params, json=json, headers=self.headers, timeout=Config.TIMEOUT)

        return APIResponse(
            data=response.json(),
            status_code=response.status_code,
            url=response.url,
            headers=response.headers,
            cookies=response.cookies,
            encoding=response.encoding,
            elapsed_seconds=response.elapsed.total_seconds(),
            reason=response.reason,
            request=str(response.request.method),
            request_params=params
        )

    def put(self, endpoint, data=None):
        """
        Perform a PUT request to the specified endpoint.

        :param endpoint: API endpoint path.
        :type endpoint: str
        :param data: Optional JSON payload to send in the request body.
        :type data: dict, optional
        :returns: API response with data, status code, and metadata.
        :rtype: APIResponse
        """
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        response = self.session.put(url, json=data, headers=self.headers, timeout=Config.TIMEOUT)

        return APIResponse(
            data=response.json(),
            status_code=response.status_code,
            url=response.url,
            headers=response.headers,
            cookies=response.cookies,
            encoding=response.encoding,
            elapsed_seconds=response.elapsed.total_seconds(),
            reason=response.reason,
            request=str(response.request.method),
            request_payload=data
        )

    def delete(self, endpoint, data=None, params=None):
        """
        Perform a DELETE request to the specified endpoint.

        :param endpoint: API endpoint path.
        :type endpoint: str
        :param data: Optional data payload to send in the request body.
        :type data: dict, optional
        :param params: Optional query parameters.
        :type params: dict, optional
        :returns: API response with data, status code, and metadata.
        :rtype: APIResponse
        """
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        response = self.session.delete(url, headers=self.headers, data=data, timeout=Config.TIMEOUT)

        return APIResponse(
            data=response.json(),
            status_code=response.status_code,
            url=response.url,
            headers=response.headers,
            cookies=response.cookies,
            encoding=response.encoding,
            elapsed_seconds=response.elapsed.total_seconds(),
            reason=response.reason,
            request=str(response.request.method),
            request_params=params
        )