"""
Base API Module
===============

This module provides the foundation for all API interactions with the Movie Database.

.. module:: api.base_api
   :synopsis: Base API client with common HTTP methods.
   :no-index:
"""

import re

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

    # Credential query params whose values must never surface in logs, test
    # failure reprs, or report attachments.
    _SECRET_QUERY_PARAMS = ("session_id",)

    @staticmethod
    def _redact_params(params):
        """
        Return a copy of ``params`` with credential values masked.

        Non-dict values (including ``None``) are returned unchanged.

        :param params: Query parameters sent with the request.
        :type params: dict, optional
        :returns: Params with any :data:`_SECRET_QUERY_PARAMS` value replaced
                  by ``<hidden>``. Example::

                      {"page": 1, "session_id": "<hidden>"}
        :rtype: dict or the original value
        """
        if not isinstance(params, dict):
            return params
        return {
            # comprehensions: expression-first, loop-last. Inverted execution order.
            # Reading rule: for clause first, then read the leading expression.
            key: "<hidden>" if key in BaseAPI._SECRET_QUERY_PARAMS else value
            for key, value in params.items()
        }

    @staticmethod
    def _redact_url(url):
        """
        Mask credential query-param values inside a URL string.

        :param url: Full request URL, possibly containing secret query params.
        :type url: str
        :returns: URL with any :data:`_SECRET_QUERY_PARAMS` value replaced by
                  ``<hidden>``. Example::

                      "https://api.themoviedb.org/3/account/42/rated/movies?session_id=<hidden>"
        :rtype: str
        """
        pattern = rf"\b({'|'.join(BaseAPI._SECRET_QUERY_PARAMS)})=[^&]+"
        return re.sub(pattern, r"\1=<hidden>", url)

    @staticmethod
    def _build_response(response, params=None, payload=None):
        """
        Adapter that turns a raw requests.Response into the repo's own APIResponse dataclass.
        Build a standardized APIResponse from a raw requests Response object.

        Credential query params (see :data:`_SECRET_QUERY_PARAMS`) are masked
        in both ``url`` and ``request_params``, so an APIResponse can be
        logged, printed in a failing assertion, or attached to a report
        without leaking a secret.

        :param response: Raw response from the requests library.
        :type response: requests.Response
        :param params: Query parameters sent with the request.
        :type params: dict, optional
        :param payload: JSON payload sent with the request body.
        :type payload: dict, optional
        :returns: Standardized API response with data, status code, and metadata.
                  ``data`` holds the parsed JSON body; credentials in ``url`` /
                  ``request_params`` are masked. Example return::

                      APIResponse(
                          data={"id": 550, "title": "Fight Club"},
                          status_code=200,
                          url="https://api.themoviedb.org/3/movie/550",
                          headers={"Content-Type": "application/json;charset=utf-8"},
                          cookies=<RequestsCookieJar>,
                          encoding="utf-8",
                          elapsed_seconds=0.12,
                          reason="OK",
                          request="GET",
                          request_params={"page": 1},
                          request_payload=None,
                      )
        :rtype: APIResponse
        """
        return APIResponse(
            data=response.json(),
            status_code=response.status_code,
            url=BaseAPI._redact_url(response.url),
            headers=response.headers,
            cookies=response.cookies,
            encoding=response.encoding,
            elapsed_seconds=response.elapsed.total_seconds(),
            reason=response.reason,
            request=str(response.request.method),
            request_params=BaseAPI._redact_params(params),
            request_payload=payload
        )

    def get(self, endpoint, params=None):
        """
        Perform a GET request to the specified endpoint.

        :param endpoint: API endpoint path.
        :type endpoint: str
        :param params: Optional query parameters.
        :type params: dict, optional
        :returns: API response with data, status code, and metadata.
                  Example return::

                      APIResponse(
                          data={"page": 1, "results": [{"id": 550, "title": "Fight Club"}]},
                          status_code=200,
                          url="https://api.themoviedb.org/3/movie/popular?page=1",
                          elapsed_seconds=0.12,
                          reason="OK",
                          request="GET",
                          request_params={"page": 1},
                          request_payload=None,
                      )
        :rtype: APIResponse
        """
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        response = self.session.get(url, headers=self.headers, params=params, timeout=Config.TIMEOUT)

        return self._build_response(response, params=params)

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
                  Example return::

                      APIResponse(
                          data={"success": True, "status_code": 1, "status_message": "Success."},
                          status_code=201,
                          url="https://api.themoviedb.org/3/movie/550/rating",
                          elapsed_seconds=0.15,
                          reason="Created",
                          request="POST",
                          request_params=None,
                          request_payload={"value": 8.5},
                      )
        :rtype: APIResponse
        """
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        response = self.session.post(url, params=params, json=json, headers=self.headers, timeout=Config.TIMEOUT)

        return self._build_response(response, params=params, payload=json)

    def put(self, endpoint, data=None):
        """
        Perform a PUT request to the specified endpoint.

        :param endpoint: API endpoint path.
        :type endpoint: str
        :param data: Optional JSON payload to send in the request body.
        :type data: dict, optional
        :returns: API response with data, status code, and metadata.
                  Example return::

                      APIResponse(
                          data={"success": True, "status_code": 12,
                                "status_message": "The item/record was updated successfully."},
                          status_code=201,
                          url="https://api.themoviedb.org/4/list/123",
                          elapsed_seconds=0.20,
                          reason="Created",
                          request="PUT",
                          request_params=None,
                          request_payload={"description": "Updated description"},
                      )
        :rtype: APIResponse
        """
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        response = self.session.put(url, json=data, headers=self.headers, timeout=Config.TIMEOUT)

        return self._build_response(response, payload=data)

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
                  Example return::

                      APIResponse(
                          data={"success": True, "status_code": 13,
                                "status_message": "The item/record was deleted successfully."},
                          status_code=200,
                          url="https://api.themoviedb.org/3/movie/550/rating",
                          elapsed_seconds=0.14,
                          reason="OK",
                          request="DELETE",
                          request_params=None,
                          request_payload=None,
                      )
        :rtype: APIResponse
        """
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        response = self.session.delete(url, headers=self.headers, params=params, data=data, timeout=Config.TIMEOUT)

        return self._build_response(response, params=params, payload=data)