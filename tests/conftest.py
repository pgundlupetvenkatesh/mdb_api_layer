import json
import pytest
from pathlib import Path
from datetime import datetime

from tests.data.data_loader import load_test_data

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