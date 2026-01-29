import os
from typing import List

class Config:
    BASE_URL: str = os.getenv('TMDB_BASE_URL', "https://api.themoviedb.org/3")
    API_KEY: str = os.getenv('TMDB_API_KEY', "818cb9ec8ef44f47f9c2b3dc8c832ed6")
    TIMEOUT: int = int(os.getenv("TMDB_TIMEOUT", "30"))  # in seconds
    ACCOUNT_ID: str = os.getenv("TMDB_ACCOUNT_ID", "12016691")
    MOVIE_ID: str = os.getenv("TMDB_MOVIE_ID", "346698")
    SESSION_ID: str = os.getenv("TMDB_SESSION_ID", "f756f92500f2e9c4d11a38582e5f4e112b10e82d")
    AUTH_TOKEN: str = os.getenv("TMDB_AUTH_TOKEN",
                                "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI4MThjYjllYzhlZjQ0ZjQ3ZjljMmIzZGM4YzgzMmVkNiIsIm5iZiI6MTY0NjE3NjQ3Mi4xMDksInN1YiI6IjYyMWVhOGQ4MDc2Y2U4MDAxYmEzNWM5ZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.vuo8RY6Tk_hBVZI_hDd56dSpfbarmBIg4yJyNTl4rqg")
    REQUEST_TOKEN: str = os.getenv("TMDB_REQ_TOKEN", "8cf8535c3a7301f13b3441f7eeda9dd6317cada8")

    @classmethod
    def validate(cls, required: List[str] = None) -> None:
        required = required or ["API_KEY"]
        missing = [name for name in required if getattr(cls, name, None) in (None, "")]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")