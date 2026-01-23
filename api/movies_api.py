from api.base_api import BaseAPI

class MoviesAPI(BaseAPI):
    _sub_path = "movie"

    def get_movie_details(self, movie_id):
        return self.get(f"{self._sub_path}/{movie_id}")

    def get_popular_movies(self, query_params=None):
        query_params ={ 'page': 1, **(query_params or {})}
        return self.get(f"{self._sub_path}/popular", params=query_params)

    def get_top_rated_movies(self, query_params=None):
        query_params ={ 'page': 1 , **(query_params or {})}
        return self.get(f"{self._sub_path}/top_rated", params=query_params)

    def get_movie_by_alt_title(self, movie_id):
        return self.get(f"{self._sub_path}/{movie_id}/alternative_titles")
