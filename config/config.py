import os
from typing import List

class Config:
    BASE_URL: str = os.getenv('TMDB_BASE_URL', "https://api.themoviedb.org/3")
    API_KEY: str = os.getenv('TMDB_API_KEY', "")
    TIMEOUT: int = int(os.getenv("TMDB_TIMEOUT", "30"))  # in seconds
    ACCOUNT_ID: str = os.getenv("TMDB_ACCOUNT_ID", "")
    MOVIE_ID: str = os.getenv("TMDB_MOVIE_ID", "")
    SESSION_ID: str = os.getenv("TMDB_SESSION_ID", "]")
    AUTH_TOKEN: str = os.getenv("TMDB_AUTH_TOKEN", "")
    REQUEST_TOKEN: str = os.getenv("TMDB_REQ_TOKEN", "")

    @classmethod
    def validate(cls, required: List[str] = None) -> None:
        required = required or ["API_KEY"]
        missing = [name for name in required if getattr(cls, name, None) in (None, "")]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")