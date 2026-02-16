from api.base_api import BaseAPI

class AccountAPI(BaseAPI):
    _sub_path = "account"

    def get_rated_movies(self, session_id, query_params=None):
        """
        Retrieve a paginated list of movies rated by the user.

        :param session_id: Optional path parameter (e.g., account ID).
        :param query_params: Optional dict of query parameters.
                             Defaults to page 1 if not specified.
        :return: Response object with paginated list of rated movies.
        """
        query_params = {'page': 1, **(query_params or {})}
        # print(f"get_rated_movies query_params: {query_params}")
        return self.get(f"{self._sub_path}/{session_id}/rated/movies", params=query_params)
