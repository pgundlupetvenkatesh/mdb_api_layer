# mdb_api_layer

[![TMDB Tests](https://github.com/pgundlupetvenkatesh/mdb_api_layer/actions/workflows/tmdb_test.yml/badge.svg)](https://github.com/pgundlupetvenkatesh/mdb_api_layer/actions/workflows/tmdb_test.yml)

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

## Installation

```bash
# Clone the repository
git clone https://github.com/pgundlupetvenkatesh/mdb_api_layer.git
cd mdb_api_layer

# Install dependencies
poetry install

# Add new Python package dependencies
poetry add <package_name>

## Testing
poetry run pytest tests/test_movies.py -v -s
```
### Sanity Checks

```
poetry env info
poetry show
```

## Configuration

### Getting TMDB API Credentials

1. **Create a TMDB account** at [themoviedb.org](https://www.themoviedb.org/signup)
2. **Request an API key:**
   - Go to [Settings → API](https://www.themoviedb.org/settings/api)
   - Click "Create" or "Request an API Key"
   - Choose "Developer" for personal/testing use
   - Fill in the application details (use your project URL or localhost for testing)
   - Once approved, you'll receive your **API Key (v3 auth)** and **API Read Access Token**
3. **Locate your credentials:**
   - **API Key**: Found under "API Key (v3 auth)" on the API settings page
   - **Auth Token**: Found under "API Read Access Token (v4 auth)" — this is your Bearer token

### Setting Up Environment Variables

Create a `.env` file in the project root (this file is gitignored):

```bash
# Required
TMDB_API_KEY=your_api_key_here
TMDB_AUTH_TOKEN=your_read_access_token_here

# Optional (defaults shown)
TMDB_BASE_URL=https://api.themoviedb.org/3
TMDB_TIMEOUT=30
```

**Alternative:** Export variables directly in your terminal:

```bash
export TMDB_API_KEY="your_api_key_here"
export TMDB_AUTH_TOKEN="your_read_access_token_here"
```

### Environment Variables Reference

| Variable          | Description                           | Required | Default                        |
|-------------------|---------------------------------------|----------|--------------------------------|
| `TMDB_API_KEY`    | Your TMDB API key (v3 auth)           | Yes      | -                              |
| `TMDB_AUTH_TOKEN` | API Read Access Token (v4 auth)       | Yes      | -                              |
| `TMDB_BASE_URL`   | API base URL                          | No       | `https://api.themoviedb.org/3` |
| `TMDB_TIMEOUT`    | Request timeout in seconds            | No       | `30`                           |
| `TMDB_ACCOUNT_ID` | TMDB account ID                       | No       | -                              |
| `TMDB_SESSION_ID` | Session ID for authenticated requests | No       | -                              |
| `TMDB_REQ_TOKEN`  | Request token for authentication      | No       | -                              |
| `TMDB_MOVIE_ID`   | Default movie ID for tests            | No       | -                              |

## Logging

The framework uses [Loguru](https://github.com/Delgan/loguru) for structured logging with colored output.

### Log Levels

| Level    | Description                          |
|----------|--------------------------------------|
| DEBUG    | Detailed diagnostic information      |
| INFO     | General operational messages         |
| WARNING  | Potential issues                     |
| ERROR    | Error events                         |
| CRITICAL | Serious failures                     |

### Log level hierarchy
| Level Set | Logs Shown                            |
|-----------|---------------------------------------|
| DEBUG     | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| INFO      | INFO, WARNING, ERROR, CRITICAL        |
| WARNING   | WARNING, ERROR, CRITICAL              |
| ERROR     | ERROR, CRITICAL                       |
| CRITICAL  | CRITICAL only                         |

### Controlling Log Level

* Default (INFO) - `poetry run pytest tests/*`
* Debug logging - `poetry run pytest tests/* --loguru-log-level=DEBUG`
* Only errors - `poetry run pytest tests/* --loguru-log-level=ERROR`

### Running Tests After Setup

```bash
# Verify your setup
poetry install

# Run tests
poetry run pytest tests/test_movies.py -v -s
```

> **Note:** Keep your API credentials secure. Never commit `.env` files or expose tokens in public repositories.

## Project Structure

```
mdb_api_layer/
├── api/
│   ├── base_api.py # Base API client with HTTP methods
│   └── movies_api.py # Movies endpoint implementation
├── config/
│   └── config.py # Environment configuration
├── tests/
│   ├── conftest.py # Pytest fixtures 
│   ├── data/ 
│   │ └── movies_test_data.yaml # Test data for movie tests 
│   ├── schemas/ 
│   │ └── movie_schema.json # JSON schema for validation 
│   └── test_movies.py # Movie API tests 
├── docs/ 
│   ├── conf.py # Sphinx configuration 
│   ├── index.rst # Documentation index 
│   ├── api.rst # API module documentation 
│   ├── config.rst # Config module documentation 
│   ├── tests.rst # Tests module documentation 
│   ├── make.bat # Windows build script 
│   └── Makefile # Unix build script 
├── .env # Environment variables (not committed) 
├── .gitignore 
├── pyproject.toml # Poetry configuration 
├── poetry.lock 
└── README.md
```

## Running Tests

```commandline
# Run all movie tests with verbose output
poetry run pytest tests/test_movies.py -v -s

# Run a specific test function
poetry run pytest tests/test_movies.py::TestClassName::test_func_name -v -s

# Run with HTML report
poetry run pytest tests/test_movies.py --html=report.html

# Run with Allure reporting
poetry run pytest tests/test_movies.py --alluredir=allure-results
allure serve allure-results
```

## Dependencies

- requests
- pytest
- pytest-html
- allure-pytest
- python-dotenv
- jsonschema
- pyyaml
- sphinx

## Documentation

```commandline
cd docs
make html
```
### View documentation
Open `docs/_build/html/index.html` in your web browser.
![doc_sample](doc_sample.png)

## Reports

### HTML Report
```bash
poetry run pytest tests/test_movies.py --html=report/tmdb_report.html --self-contained-html -v -s
```

Generate a simple pytest HTML test report:
Open the generated `tmdb_report.html` in your web browser to view the test results.
![sample_report](sample_report.png)
