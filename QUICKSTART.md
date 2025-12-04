# Quick Start Guide

## Get Started in 5 Minutes

### 1. Get Your API Key
Visit http://www.omdbapi.com/apikey.aspx and sign up for a free API key.

### 2. Set Up Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# OMDB_API_KEY=your_actual_api_key_here
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Example Script
```bash
python example.py
```

### 5. Run the Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only smoke tests
pytest -m smoke

# Generate HTML report
pytest --html=report.html --self-contained-html
```

## What's Included

- **28 comprehensive test cases** covering:
  - Search functionality (movie search, filters, pagination)
  - Movie details (by ID, by title, with various parameters)
  - Error handling and edge cases
  
- **Clean API client** with methods for:
  - `search_movies()` - Search for movies
  - `get_by_id()` - Get details by IMDB ID
  - `get_by_title()` - Get details by title

- **Test organization** with markers:
  - `smoke` - Critical functionality tests
  - `regression` - Regression test suite
  - `search` - Search-related tests
  - `details` - Movie details tests

## Next Steps

1. Check out the [README.md](README.md) for detailed documentation
2. Look at [example.py](example.py) to see how to use the API client
3. Explore the tests in the `tests/` directory for examples
4. Start writing your own tests!

## Common Commands

```bash
# Run specific test file
pytest tests/test_search.py

# Run tests with specific marker
pytest -m smoke

# Run tests and show print statements
pytest -v -s

# Run tests with coverage (requires pytest-cov)
pytest --cov=src

# List all available tests
pytest --collect-only
```

## Troubleshooting

**Tests are skipped?**
- Make sure your `.env` file has the `OMDB_API_KEY` set

**Import errors?**
- Make sure you installed dependencies: `pip install -r requirements.txt`

**API key not working?**
- Verify your API key is active at http://www.omdbapi.com/
- Free keys have usage limits (1,000 requests per day)

## Need Help?

Check the [README.md](README.md) for more detailed information or open an issue on GitHub.
