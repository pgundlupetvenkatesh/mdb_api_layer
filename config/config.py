import os
import sys

from typing import List
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def configure_logging():
    """
    Configure loguru logger with custom format and log level.

    Removes the default loguru handler and adds a new one with:
    - Colored output to stderr
    - Custom format: timestamp | level | module:function:line - message
    - Log level from LOG_LEVEL environment variable (defaults to INFO)

    Log levels (threshold-based, shows specified level and above):
        - DEBUG: Detailed diagnostic information
        - INFO: General operational messages (default)
        - WARNING: Potential issues
        - ERROR: Error events
        - CRITICAL: Serious failures

    Can be called multiple times to reconfigure logging (e.g., after
    setting LOG_LEVEL environment variable in pytest_configure).

    :return: None

    Example:
        os.environ["LOG_LEVEL"] = "DEBUG"
        configure_logging()  # Now shows DEBUG and above
    """
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=os.getenv('LOG_LEVEL', 'INFO'),
        colorize=True
    )

configure_logging()

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