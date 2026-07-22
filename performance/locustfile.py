"""
Locust load-test scenarios for the TMDB movies endpoints.

Two user models, selectable by class name on the CLI (running without a class
name spawns both 50/50.

- ``MoviesUser`` — endpoint traffic mix: weighted, independent read-only
  requests mirroring ``api/movies_api.py``. The original baselining model.
- ``JourneyUser`` — realistic user journeys: four ``SequentialTaskSet``
  flows (browse & drill down, search-driven, filtered discovery, cast
  exploration) where later steps chain ids taken from earlier responses.

Both use Locust's own ``self.client`` (not the API classes) so every
request is instrumented for the stats report; auth and URLs are still
single-sourced from ``config.config.Config`` / ``.env``.

Target is the live TMDB API — keep the load gentle (see performance/README.md).

Run from the repo root:
    poetry run locust -f performance/locustfile.py JourneyUser            # web UI at :8089
    poetry run locust -f performance/locustfile.py MoviesUser --headless -u 3 -r 1 -t 30s
"""

import random

from locust import HttpUser, SequentialTaskSet, between, task

from config.config import Config
from tests.data.data_loader import load_test_data
from tests.helpers.test_data_generators import pick_random_movie_id

API = f"/{Config.API_VERSION}"

# Rotating search queries, single-sourced from the integration suite's data so
# perf and functional tests exercise the same known-good query set.
SEARCH_QUERIES = sorted({
    case["query_param"]["query"]
    for case in load_test_data("test_data.yaml", "search_movies")["search_movies"]["valid"]
})

# Filter combinations for the discovery journey (genre ids: action, comedy,
# sci-fi). Values are strings — requests would serialize Python bools/ints
# in forms TMDB only tolerates undocumented.
DISCOVER_FILTERS = (
    {"with_genres": "28", "sort_by": "popularity.desc"},
    {"with_genres": "35", "primary_release_year": "2020"},
    {"with_genres": "878", "sort_by": "vote_average.desc", "vote_count.gte": "1000"},
)


def _auth_headers():
    """
    Build the default headers for every simulated user's session.

    Also fail-fast validates the credential, so a missing ``TMDB_AUTH_TOKEN``
    aborts at user spawn instead of surfacing as per-request 401 failures.
    (Validation is deliberately not at module import time: Sphinx imports this
    module to render docs and must not require a configured ``.env``.)

    :returns: Headers with Bearer authorization and JSON content type.
    :rtype: dict
    :raises RuntimeError: If ``TMDB_AUTH_TOKEN`` is not configured.
    """
    Config.validate(["AUTH_TOKEN"])
    return {
        "Authorization": f"Bearer {Config.AUTH_TOKEN}",
        "Content-Type": "application/json",
    }


def _pick_result_id(response, key="results"):
    """
    Pull a random item id out of a paginated response.

    Used to chain journey steps: the id picked from one step's response
    becomes the path parameter of the next step's request.

    :param response: Response from an instrumented ``self.client`` call.
    :type response: requests.Response
    :param key: Body key holding the list of items to pick from.
    :type key: str
    :returns: A random item's ``id``, or ``None`` when the request failed or
              the list is missing/empty (callers skip their step on ``None``).
    :rtype: int or None
    """
    items = response.json().get(key) if response.ok else None
    return random.choice(items)["id"] if items else None


class BrowseAndDrillDown(SequentialTaskSet):
    """Casual visitor: popular list → details of a listed movie → its alt titles."""

    @task
    def popular_page(self):
        """Fetch page 1 of popular movies and remember a random listed id."""
        response = self.client.get(f"{API}/movie/popular", params={"page": 1})
        self.movie_id = _pick_result_id(response)

    @task
    def movie_details(self):
        """Open the details of the movie picked from the popular list."""
        if self.movie_id:
            self.client.get(f"{API}/movie/{self.movie_id}", name=f"{API}/movie/[id]")

    @task
    def alternative_titles(self):
        """
        Fetch the picked movie's alternative titles, then end the journey.

        :raises locust.exception.InterruptTaskSet: Always, via
            ``self.interrupt()``, returning control to the user class so its
            next journey can be scheduled.
        """
        if self.movie_id:
            self.client.get(
                f"{API}/movie/{self.movie_id}/alternative_titles",
                name=f"{API}/movie/[id]/alternative_titles",
            )
        self.interrupt() # Ends the journey and helps to put the execution back to the user class to pick the next one.


class SearchDriven(SequentialTaskSet):
    """Searcher: query page 1 → page 2 of the same query → details of a result."""

    @task
    def search_first_page(self):
        """Search a rotating query and remember a random matched movie id."""
        self.query = random.choice(SEARCH_QUERIES)
        response = self.client.get(
            f"{API}/search/movie",
            params={"query": self.query, "page": 1},
            name=f"{API}/search/movie",
        )
        self.movie_id = _pick_result_id(response)

    @task
    def search_second_page(self):
        """Paginate to page 2 of the same query, like a user scanning on."""
        self.client.get(
            f"{API}/search/movie",
            params={"query": self.query, "page": 2},
            name=f"{API}/search/movie",
        )

    @task
    def movie_details(self):
        """
        Open the details of the picked search result, then end the journey.

        :raises locust.exception.InterruptTaskSet: Always, via
            ``self.interrupt()``.
        """
        if self.movie_id:
            self.client.get(f"{API}/movie/{self.movie_id}", name=f"{API}/movie/[id]")
        self.interrupt()


class FilteredDiscovery(SequentialTaskSet):
    """Undecided browser: filtered discover → two more pages → details of a hit."""

    @task
    def discover_first_page(self):
        """Run a random filter combination and remember a random hit's id."""
        self.filters = random.choice(DISCOVER_FILTERS)
        response = self.client.get(
            f"{API}/discover/movie",
            params={**self.filters, "page": 1},
            name=f"{API}/discover/movie",
        )
        self.movie_id = _pick_result_id(response)

    @task
    def discover_more_pages(self):
        """Page through results 2–3 with the same filters, back-to-back."""
        for page in (2, 3):
            self.client.get(
                f"{API}/discover/movie",
                params={**self.filters, "page": page},
                name=f"{API}/discover/movie",
            )

    @task
    def movie_details(self):
        """
        Open the details of the picked discover hit, then end the journey.

        :raises locust.exception.InterruptTaskSet: Always, via
            ``self.interrupt()``.
        """
        if self.movie_id:
            self.client.get(f"{API}/movie/{self.movie_id}", name=f"{API}/movie/[id]")
        self.interrupt()


class CastExploration(SequentialTaskSet):
    """Rabbit-hole user: movie details → its credits → a cast member's details."""

    @task
    def movie_details(self):
        """Open a random movie's details (id drawn from movie_ids.txt)."""
        self.movie_id = pick_random_movie_id()
        self.client.get(f"{API}/movie/{self.movie_id}", name=f"{API}/movie/[id]")

    @task
    def movie_credits(self):
        """Fetch the movie's credits and remember a random cast member's id."""
        response = self.client.get(
            f"{API}/movie/{self.movie_id}/credits",
            name=f"{API}/movie/[id]/credits",
        )
        self.person_id = _pick_result_id(response, key="cast")

    @task
    def person_details(self):
        """
        Open the picked cast member's person details, then end the journey.

        :raises locust.exception.InterruptTaskSet: Always, via
            ``self.interrupt()``.
        """
        if self.person_id:
            self.client.get(f"{API}/person/{self.person_id}", name=f"{API}/person/[id]")
        self.interrupt()


class JourneyUser(HttpUser):
    """
    A simulated visitor running complete browse sessions.

    Each iteration picks one journey by weight (~50/25/15/10 user mix) and
    runs its steps in order with think-time between them; ids for later steps
    come from earlier responses, so the traffic is correlated like a real
    client's. Write endpoints stay excluded — no mutation load on the live API.
    """

    host = Config.BASE_URL
    wait_time = between(1, 3)  # seconds of think-time between journey steps
    tasks = {
        BrowseAndDrillDown: 10,
        SearchDriven: 5,
        FilteredDiscovery: 3,
        CastExploration: 2,
    }

    def on_start(self):
        """Attach auth headers to this user's session once, at spawn time."""
        self.client.headers.update(_auth_headers())


class MoviesUser(HttpUser):
    """
    A simulated TMDB API consumer issuing independent movie requests.

    Task weights approximate real read traffic: movie details requested most,
    list endpoints less often. Write endpoints (rating add/delete) are
    deliberately excluded — no mutation load on the live API.
    """

    host = Config.BASE_URL
    wait_time = between(1, 3)  # seconds of think-time between each user's tasks

    def on_start(self):
        """Attach auth headers to this user's session once, at spawn time."""
        self.client.headers.update(_auth_headers())

    @task(3)
    def movie_details(self):
        """Fetch details of a random movie (weight 3: the dominant request)."""
        # Random ids from tests/data/movie_ids.txt bust server-side caches;
        # `name=` groups all of them under one row in the stats table.
        self.client.get(
            f"{API}/movie/{pick_random_movie_id()}",
            name=f"{API}/movie/[id]",
        )

    @task(2)
    def popular_movies(self):
        """
        Fetch page 1 of popular movies, with custom pass/fail judgment.

        Demonstrates ``catch_response``: a 200 whose body has no ``results``
        is marked a failure even though the status code alone would pass.
        """
        with self.client.get(
            f"{API}/movie/popular",
            params={"page": 1},
            catch_response=True,
        ) as response:
            if response.ok and not response.json().get("results"):
                response.failure("200 OK but 'results' is missing or empty")

    @task(1)
    def top_rated_movies(self):
        """Fetch page 1 of top-rated movies."""
        self.client.get(f"{API}/movie/top_rated", params={"page": 1})

    @task(1)
    def alternative_titles(self):
        """Fetch alternative titles for the fixed ``Config.MOVIE_ID`` movie."""
        self.client.get(
            f"{API}/movie/{Config.MOVIE_ID}/alternative_titles",
            name=f"{API}/movie/[id]/alternative_titles",
        )