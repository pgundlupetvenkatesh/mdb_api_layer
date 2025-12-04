"""Configuration management for OMDB API testing."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for API testing."""
    
    OMDB_API_KEY = os.getenv('OMDB_API_KEY', '')
    OMDB_BASE_URL = os.getenv('OMDB_BASE_URL', 'http://www.omdbapi.com/')
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.OMDB_API_KEY:
            raise ValueError(
                "OMDB_API_KEY not found. Please set it in .env file or environment variables. "
                "Get your free API key from: http://www.omdbapi.com/apikey.aspx"
            )
        return True
