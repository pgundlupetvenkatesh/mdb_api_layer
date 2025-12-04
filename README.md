# OMDB API Testing Framework

API Testing framework for the Open Movie Database (OMDB) API using Python, pytest, and requests.

## Overview

This project provides a comprehensive API testing framework for [OMDB API](http://www.omdbapi.com/) with the following features:

- **API Client**: Easy-to-use Python client for interacting with OMDB API
- **Test Suite**: Comprehensive test cases covering search, movie details, and edge cases
- **Configuration Management**: Environment-based configuration for API keys and endpoints
- **Utility Functions**: Helper functions for response validation
- **Test Markers**: Organized tests with markers for smoke, regression, and functional testing

## Project Structure

```
mdb_api_layer/
├── src/
│   ├── api_client/          # OMDB API client
│   │   ├── __init__.py
│   │   └── omdb_client.py
│   ├── config/              # Configuration management
│   │   ├── __init__.py
│   │   └── config.py
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── validators.py
├── tests/                   # Test suite
│   ├── conftest.py         # Pytest fixtures
│   ├── test_api_client.py  # Client initialization tests
│   ├── test_search.py      # Search functionality tests
│   └── test_movie_details.py  # Movie details tests
├── .env.example            # Environment variables template
├── pytest.ini              # Pytest configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- OMDB API Key (get one free at http://www.omdbapi.com/apikey.aspx)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/pgundlupetvenkatesh/mdb_api_layer.git
   cd mdb_api_layer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OMDB API key:
   ```
   OMDB_API_KEY=your_actual_api_key_here
   OMDB_BASE_URL=http://www.omdbapi.com/
   ```

## Usage

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run tests with verbose output:**
```bash
pytest -v
```

**Run specific test markers:**
```bash
# Run only smoke tests
pytest -m smoke

# Run only search tests
pytest -m search

# Run only movie details tests
pytest -m details

# Run regression tests
pytest -m regression
```

**Run tests from a specific file:**
```bash
pytest tests/test_search.py
pytest tests/test_movie_details.py
pytest tests/test_api_client.py
```

**Generate HTML test report:**
```bash
pytest --html=report.html --self-contained-html
```

### Using the API Client

You can use the OMDB client in your own scripts:

```python
from src.api_client import OMDBClient

# Initialize the client
client = OMDBClient(api_key='your_api_key')

# Search for movies
response = client.search_movies('Batman')
print(response.json())

# Get movie by ID
response = client.get_by_id('tt0111161')  # The Shawshank Redemption
print(response.json())

# Get movie by title
response = client.get_by_title('The Matrix', year='1999')
print(response.json())
```

## API Client Methods

### OMDBClient

**`search_movies(search_term, year=None, page=1, content_type=None)`**
- Search for movies by title
- Parameters:
  - `search_term`: Movie title to search for
  - `year`: Year of release (optional)
  - `page`: Page number for results (default: 1)
  - `content_type`: Type of result - 'movie', 'series', or 'episode' (optional)

**`get_by_id(imdb_id, plot='short')`**
- Get movie details by IMDB ID
- Parameters:
  - `imdb_id`: IMDB ID (e.g., 'tt1285016')
  - `plot`: Plot length - 'short' or 'full' (default: 'short')

**`get_by_title(title, year=None, plot='short', content_type=None)`**
- Get movie details by title
- Parameters:
  - `title`: Movie title
  - `year`: Year of release (optional)
  - `plot`: Plot length - 'short' or 'full' (default: 'short')
  - `content_type`: Type of result - 'movie', 'series', or 'episode' (optional)

## Test Coverage

The test suite includes:

### Search Tests (`test_search.py`)
- ✅ Successful movie search
- ✅ Search with year filter
- ✅ Search with content type filter
- ✅ Search pagination
- ✅ Search with no results
- ✅ Search with empty string
- ✅ Search with special characters
- ✅ Case-insensitive search

### Movie Details Tests (`test_movie_details.py`)
- ✅ Get movie by IMDB ID
- ✅ Get movie with full plot
- ✅ Get movie by title
- ✅ Get movie by title with year
- ✅ Get movie by title with type filter
- ✅ Invalid IMDB ID handling
- ✅ Non-existent title handling
- ✅ Response structure validation
- ✅ Ratings and metadata validation

### Client Tests (`test_api_client.py`)
- ✅ Client initialization
- ✅ Custom base URL configuration
- ✅ API key validation
- ✅ Error response handling
- ✅ Response structure validation

## Test Markers

Tests are organized with the following markers:

- `smoke`: Critical functionality tests
- `regression`: Regression test suite
- `search`: Search-related tests
- `details`: Movie details tests

## Dependencies

- **pytest**: Testing framework
- **requests**: HTTP library for API calls
- **pytest-html**: HTML report generation
- **python-dotenv**: Environment variable management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite
5. Submit a pull request

## License

This project is for educational and practice purposes.

## API Reference

For complete OMDB API documentation, visit: http://www.omdbapi.com/

## Troubleshooting

**Issue: Tests are skipped with "OMDB_API_KEY not set"**
- Solution: Make sure you have created a `.env` file with your API key

**Issue: Tests fail with "Invalid API key"**
- Solution: Verify your API key is correct and active at http://www.omdbapi.com/

**Issue: Rate limiting errors**
- Solution: Free API keys have usage limits. Wait a moment or upgrade your API key

## Contact

For questions or issues, please open an issue on the GitHub repository.
