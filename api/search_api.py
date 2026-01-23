from api.base_api import BaseAPI

class SearchAPI(BaseAPI):
    def search_movies(self, query_params):
        return self.get("/search/movie", params=query_params)