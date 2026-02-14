"""
Test data generators for dynamic test values.
"""
import random

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

def pick_random_movie_id() -> int:
    """
    Reads numbers from a tests/data/movie_ids.txt file and returns a random one.
    Assumes one number per line.

    :return: Random movie ID
    :raises FileNotFoundError: If movie_ids.txt doesn't exist
    :raises ValueError: If file is empty or contains invalid data
    """
    from pathlib import Path

    file_path = Path(__file__).parent.parent / "data" / "movie_ids.txt"

    # Open the file and read all lines into a list
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Strip whitespace (like newline characters) and convert to integers
    numbers = [int(line.strip()) for line in lines if line.strip()]

    if not numbers:
        raise ValueError("movie_ids.txt is empty or contains no valid numbers.")

    return random.choice(numbers)

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