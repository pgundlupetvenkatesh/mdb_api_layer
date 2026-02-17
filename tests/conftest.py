import json
import os
import pytest

from pathlib import Path
from datetime import datetime

# Registering logger configuration options and setup before any test runs
def pytest_addoption(parser):
    """
    Register custom command-line options for pytest.

    Adds --loguru-log-level option to control application logging verbosity
    during test runs. This hook runs during pytest's startup phase before
    any tests are collected.

    :param parser: Pytest's argument parser instance.

    Usage:
        poetry run pytest tests/* --loguru-log-level=DEBUG
        poetry run pytest tests/* --loguru-log-level=WARNING
        poetry run pytest tests/* --log-to-file

    Available log levels:
        DEBUG, INFO (default), WARNING, ERROR, CRITICAL
    """
    parser.addoption(
        "--loguru-log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set log level for tests"
    )
    parser.addoption(
        "--log-to-file",
        action="store_true",
        default=False,
        help="Enable logging to file (default: False)"
    )

# Set LOG_LEVEL to environment variable before any test modules are imported, ensuring loguru is configured correctly
def pytest_configure(config):
    """
    Configure the test environment before test collection begins.

    Sets the LOG_LEVEL environment variable based on the --loguru-log-level
    CLI option, then reconfigures loguru to use the new level. This ensures
    logging is properly configured before any test modules are imported.

    :param config: Pytest's Config object containing parsed CLI options.

    Note:
        This hook runs after pytest_addoption but before test collection.
        The configure_logging() call is necessary because loguru may have
        already been initialized with default settings at module import time.
    """
    os.environ["LOG_LEVEL"] = config.getoption("--loguru-log-level")
    os.environ["LOG_TO_FILE"] = str(config.getoption("--log-to-file"))
    from config.config import configure_logging
    configure_logging()

from tests.data.data_loader import load_test_data
from api.movies_api import MoviesAPI
from api.account_api import AccountAPI

@pytest.fixture
def movies_api():
    """
    Fixture that provides a MoviesAPI instance for each test.

    Creates a fresh API client before each test and yields it for use.

    :yields: Configured MoviesAPI instance.
    """
    api = MoviesAPI()
    yield api


@pytest.fixture
def account_api():
    """
    Fixture that provides an AccountAPI instance for each test.

    Creates a fresh API client before each test and yields it for use.

    :yields: Configured AccountAPI instance.
    """
    api = AccountAPI()
    yield api


@pytest.fixture
def load_schema():
    """
    Fixture that provides a schema loader function for JSON schema validation.

    Returns a callable that loads JSON schema files from the 'tests/schemas'
    directory. Used to validate API responses against expected structures.

    :return: A function that accepts a schema name (without extension) and
             returns the parsed JSON schema as a dictionary.

    Usage:
        def test_example(load_schema):
            schema = load_schema('movie_schema')
            validate(instance=response.data, schema=schema)
    """
    def _load(name):
        schema_path = Path(__file__).parent / "schemas" / f"{name}.json"
        return json.loads(schema_path.read_text())
    return _load

@pytest.fixture(scope="session")
def movies_test_data():
    """
    Session-scoped fixture that loads movies API test data from YAML.

    Loads test data once per test session and shares it across all tests,
    improving performance by avoiding repeated file reads.

    Note: This fixture is currently unused. The test module uses a module-level
    constant with @pytest.mark.parametrize instead, which is required because
    parametrize decorators are evaluated at collection time before fixtures
    are available.

    :return: Dictionary containing test data with defaults applied.
    """
    return load_test_data("movies_test_data.yaml")

def pytest_html_report_title(report):
    """
    Customize the title of the HTML test report.
    :param report:
    :return:
    """
    report.title = "Movies API Test Report"

def pytest_html_results_summary(prefix, summary, postfix):
    # Quick status header
    prefix.extend([
        "<h2>🎬 TMDB API Automation Suite</h2>",
        f"<p>Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
    ])

    # Env callout
    # Note: Passed/Failed counts are automatically added here by pytest-html
    summary.extend([
        "<h3>Report Summary</h3>",
        "<p>Validation of critical TMDB endpoints including Movies, TV, and Search services.</p>"
    ])

    # Links to doc, logs
    postfix.extend([
        "<hr>",
        "<div>",
        "  <p>For detailed API specs, visit the "
        "    <a href='https://developer.themoviedb.org'>TMDB Documentation</a>"
        "  </p>",
        "  <p style='color: #666;'>Failure logs are archived in the /logs workspace directory.</p>",
        "</div>"
    ])