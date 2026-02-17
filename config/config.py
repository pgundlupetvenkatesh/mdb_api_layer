import os
from typing import List

from dotenv import load_dotenv
load_dotenv()

# Configure logging with loguru
import sys
from loguru import logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO", # Other levels include DEBUG, WARNING, ERROR, CRITICAL
    colorize=True
)

class Config:
    BASE_URL: str = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
    TIMEOUT: int = int(os.getenv("TMDB_TIMEOUT", "30"))  # in seconds
    ACCOUNT_ID: str = os.getenv("TMDB_ACCOUNT_ID", "12016691")
    MOVIE_ID: str = os.getenv("TMDB_MOVIE_ID", "346698")

    API_KEY: str = os.getenv("TMDB_API_KEY")
    SESSION_ID: str = os.getenv("TMDB_SESSION_ID")
    AUTH_TOKEN: str = os.getenv("TMDB_AUTH_TOKEN")
    REQUEST_TOKEN: str = os.getenv("TMDB_REQ_TOKEN")

    @classmethod
    def validate(cls, required: List[str] = None) -> None:
        required = required or ["API_KEY"]
        missing = [name for name in required if getattr(cls, name, None) in (None, "")]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")