# mdb_api_layer

API Testing Framework for The Movie Database ([TMDB](https://themoviedb.org)) with Python

## Overview

A Python-based API testing framework for TMDB API, featuring structured test organization, JSON schema validation, and
comprehensive response assertions.

## Features

- RESTful API client with session management
- JSON schema validation for response structure
- Configurable environment-based settings
- Pytest integration with HTML and Allure reporting
- Sphinx documentation support

## Prerequisites

- Python 3.8+
- [Poetry](https://python-poetry.org/) for dependency management
- TMDB API account and API key

## Installation

```bash
# Clone the repository
git clone https://github.com/pgundlupetvenkatesh/mdb_api_layer.git
cd mdb_api_layer

# Install dependencies
poetry install

## Testing
`poetry run pytest tests/test_movies.py -v -s`
```
### Sanity Checks
`poetry env info`
`poetry show`

## Configuration

Set the following environment variables before running tests:

| Variable          | Description                           | Required | Default                        |
|-------------------|---------------------------------------|----------|--------------------------------|
| `TMDB_API_KEY`    | Your TMDB API key                     | Yes      | -                              |
| `TMDB_AUTH_TOKEN` | Bearer authentication token           | Yes      | -                              |
| `TMDB_BASE_URL`   | API base URL                          | No       | `https://api.themoviedb.org/3` |
| `TMDB_TIMEOUT`    | Request timeout in seconds            | No       | `30`                           |
| `TMDB_ACCOUNT_ID` | TMDB account ID                       | No       | -                              |
| `TMDB_SESSION_ID` | Session ID for authenticated requests | No       | -                              |
| `TMDB_REQ_TOKEN`  | Request token for authentication      | No       | -                              |
| `TMDB_MOVIE_ID`   | Default movie ID for tests            | No       | -                              |

```
export TMDB_API_KEY="your_api_key"
export TMDB_AUTH_TOKEN="your_auth_token"
```

## Project Structure

```
mdb_api_layer/
├── api/
│   ├── base_api.py       # Base API client with HTTP methods
│   └── movies_api.py     # Movies endpoint implementation
├── config/
│   └── config.py         # Environment configuration
├── tests/
│   ├── conftest.py       # Pytest fixtures
│   ├── schemas/          # JSON schema files
│   └── test_movies.py    # Movie API tests
├── docs/                  # Sphinx documentation
└── README.md
```

## Running Tests

```commandline
# Run all movie tests with verbose output
poetry run pytest tests/test_movies.py -v -s

# Run with HTML report
poetry run pytest tests/test_movies.py --html=report.html

# Run with Allure reporting
poetry run pytest tests/test_movies.py --alluredir=allure-results
allure serve allure-results
```

## Dependency

- requests
- pytest
- pytest-html
- allure-pytest

## Documentation

```commandline
cd docs
make html
```
### View documentation
Open `docs/_build/html/index.html` in your web browser.

## Reports

### HTML Report
```bash
poetry run pytest tests/test_movies.py --html=tmdb_report.html --self-contained-html -v -s
```

Generate a simple pytest HTML test report:
Open the generated `tmdb_report.html` in your web browser to view the test results.
![sample_report](sample_report.png)
