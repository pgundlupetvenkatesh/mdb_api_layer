"""
Test data generators for dynamic test values.
"""
import random
from functools import lru_cache
from pathlib import Path

def random_rating(min_val: float = 0.5, max_val: float = 10.0) -> float:
    """
    Generate a random valid movie rating in 0.5 increments.

    :param min_val: Minimum rating value (default: 0.5)
    :param max_val: Maximum rating value (default: 10.0)
    :return: Random rating rounded to 1 decimal place
    """
    steps = int((max_val - min_val) / 0.5) + 1
    return min_val + random.randrange(steps) * 0.5


def random_invalid_rating() -> float:
    """
    Generate a random invalid movie rating (outside 0.5-10.0 range).

    :return: Random invalid rating
    """
    if random.choice([True, False]):
        return round(random.uniform(-10.0, 0.4), 1)  # Too low
    return round(random.uniform(10.1, 20.0), 1)  # Too high

@lru_cache(maxsize=1)
def _load_movie_ids() -> tuple:
    """
    Read and cache movie IDs from tests/data/movie_ids.txt (one integer per line).

    The file (~50k lines) is read and parsed once per process; subsequent calls
    return the cached tuple, so repeated ``pick_random_movie_id`` calls don't
    re-read the file.

    :return: Tuple of movie IDs.
    :raises FileNotFoundError: If movie_ids.txt doesn't exist.
    :raises ValueError: If the file is empty or contains no valid numbers.
    """
    file_path = Path(__file__).parent.parent / "data" / "movie_ids.txt"

    with open(file_path, 'r') as file:
        numbers = tuple(int(line.strip()) for line in file if line.strip())

    if not numbers:
        raise ValueError("movie_ids.txt is empty or contains no valid numbers.")

    return numbers

def pick_random_movie_id() -> int:
    """
    Return a random movie ID from the cached movie_ids.txt list.

    The file is read once via :func:`_load_movie_ids`; each call only performs an
    in-memory random choice.

    :return: Random movie ID
    :raises FileNotFoundError: If movie_ids.txt doesn't exist
    :raises ValueError: If file is empty or contains invalid data
    """
    return random.choice(_load_movie_ids())

# Well-known, stable TMDB network IDs verified against the live API:
# ABC, BBC One, NBC, CBS, FOX, HBO, Cartoon Network, The CW, AMC, Netflix.
NETWORK_IDS = (2, 4, 6, 16, 19, 49, 56, 71, 174, 213)

def pick_random_network_id() -> int:
    """
    Return a random TMDB network ID from the hardcoded :data:`NETWORK_IDS` list.

    :return: Random network ID
    """
    return random.choice(NETWORK_IDS)

def pick_random_review_id(max_attempts: int = 25) -> str:
    """
    Return a random review ID harvested from a random movie's reviews.

    Reuses :func:`pick_random_movie_id`, then fetches that movie's reviews via
    ``GET /3/movie/{id}/reviews``. Most movies in ``movie_ids.txt`` have no
    reviews, so it retries random movies until one has at least one review, then
    returns a random review's id. ``MoviesAPI`` is imported lazily to avoid an
    import cycle (``api`` imports would otherwise load during test-data import).

    :param max_attempts: Maximum random movies to try before giving up.
    :return: A TMDB review ID (24-character hex string).
    :raises ValueError: If no reviews are found within ``max_attempts`` tries.
    """
    from api.movies_api import MoviesAPI

    movies_api = MoviesAPI()
    for _ in range(max_attempts):
        results = movies_api.get_movie_reviews(pick_random_movie_id()).data.get('results', [])
        if results:
            return random.choice(results)['id']

    raise ValueError(f"No reviews found after {max_attempts} random movies.")

def pick_random_rated_movie_id(acc_id, session_id) -> int:
    """
    Fetches rated movies from the account and returns a random movie ID.

    :return: Random rated movie ID
    :raises ValueError: If no rated movies are found
    """
    from api.account_api import AccountAPI

    account_api = AccountAPI()
    response = account_api.get_rated_movies(acc_id, query_params={'session_id': session_id})
    rated_movies = response.data.get('results', [])
    # print(f"Rated Movies: {rated_movies}")

    if not rated_movies:
        raise ValueError("No rated movies found for this account.")

    return random.choice(rated_movies)['id']