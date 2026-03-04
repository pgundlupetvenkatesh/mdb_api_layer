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
    - Optional file logging when LOG_TO_FILE is set to "True"

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
        os.environ["LOG_TO_FILE"] = "True"
        configure_logging()  # Now shows DEBUG and above, also logs to file
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_to_file = os.getenv('LOG_TO_FILE', 'False') == 'True'

    logger.remove()

    # Always log to stderr
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # Optionally log to file
    if log_to_file:
        logger.add(
            "logs/test_run.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation="5 MB",
            retention="7 days"
        )

configure_logging()

class Config:
    BASE_URL: str = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org")
    API_VERSION: str = os.getenv("TMDB_API_VERSION", "3")
    TIMEOUT: int = int(os.getenv("TMDB_TIMEOUT", "30"))  # in seconds
    ACCOUNT_ID: str = os.getenv("TMDB_ACCOUNT_ID", "12016691")
    MOVIE_ID: str = os.getenv("TMDB_MOVIE_ID", "346698")

    API_KEY: str = os.getenv("TMDB_API_KEY")
    SESSION_ID: str = os.getenv("TMDB_SESSION_ID")  # for v3 auth
    AUTH_TOKEN: str = os.getenv("TMDB_AUTH_TOKEN")
    USER_ACCESS_TOKEN: str = os.getenv("TMDB_USER_ACCESS_TOKEN")    # for v4 auth
    REQUEST_TOKEN: str = os.getenv("TMDB_REQ_TOKEN")

    @classmethod
    def validate(cls, required: List[str] = None) -> None:
        required = required or ["API_KEY"]
        missing = [name for name in required if getattr(cls, name, None) in (None, "")]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")