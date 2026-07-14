"""
Locust load-test scenarios for the TMDB movies endpoints.

Simulates API consumers issuing the same read-only requests as
``api/movies_api.py`` (details, popular, top-rated, alternative titles).
Uses Locust's own ``self.client`` (not ``MoviesAPI``) so every request is
instrumented for the stats report; auth and URLs are still single-sourced
from ``config.config.Config`` / ``.env``.

Target is the live TMDB API — keep the load gentle (see performance/README.md).

Run from the repo root:
    poetry run locust -f performance/locustfile.py                          # web UI at :8089
    poetry run locust -f performance/locustfile.py --headless -u 3 -r 1 -t 30s
"""

from locust import HttpUser, between, task

from config.config import Config
from tests.helpers.test_data_generators import pick_random_movie_id

# Fail fast at locust startup, before any simulated users spawn.
Config.validate(["AUTH_TOKEN"])

API = f"/{Config.API_VERSION}"


class TMDBMoviesUser(HttpUser):
    """
    A simulated TMDB API consumer browsing movies.

    Task weights approximate real read traffic: movie details requested most,
    list endpoints less often. Write endpoints (rating add/delete) are
    deliberately excluded — no mutation load on the live API.
    """

    host = Config.BASE_URL
    wait_time = between(1, 3)  # seconds of think-time between each user's tasks

    def on_start(self):
        self.client.headers.update({
            "Authorization": f"Bearer {Config.AUTH_TOKEN}",
            "Content-Type": "application/json",
        })

    @task(3)
    def movie_details(self):
        # Random ids from tests/data/movie_ids.txt bust server-side caches;
        # `name=` groups all of them under one row in the stats table.
        self.client.get(
            f"{API}/movie/{pick_random_movie_id()}",
            name=f"{API}/movie/[id]",
        )

    @task(2)
    def popular_movies(self):
        # catch_response example: a 200 with an empty body is still a failure.
        with self.client.get(
            f"{API}/movie/popular",
            params={"page": 1},
            catch_response=True,
        ) as response:
            if response.ok and not response.json().get("results"):
                response.failure("200 OK but 'results' is missing or empty")

    @task(1)
    def top_rated_movies(self):
        self.client.get(f"{API}/movie/top_rated", params={"page": 1})

    @task(1)
    def alternative_titles(self):
        self.client.get(
            f"{API}/movie/{Config.MOVIE_ID}/alternative_titles",
            name=f"{API}/movie/[id]/alternative_titles",
        )