"""
Pytest configuration and shared fixtures for the TMDB API test suite.

This module is automatically loaded by pytest before test collection. It provides:

- **CLI options**: ``--loguru-log-level``, ``--log-to-file``, ``--failure-analysis``, ``--judge-diagnosis``
- **Hooks**: Logging setup, AI failure analysis, end-of-run AI diagnosis console summary, Allure/HTML report customization
- **Fixtures**: API client factory, Pydantic schema loader, test data loader

.. module:: tests.conftest
   :synopsis: Pytest fixtures, hooks, and CLI options.
   :no-index:
"""

import json
import os
import pytest

from pathlib import Path
from loguru import logger
from datetime import datetime
from zoneinfo import ZoneInfo
from tests.helpers.failure_analyzer import analyzer

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
    parser.addoption(
        "--failure-analysis",
        action="store_true",
        default=False,
        help="Enable AI-powered test failure analysis (requires GROQ_API_KEY)"
    )
    parser.addoption(
        "--judge-diagnosis",
        action="store_true",
        default=False,
        help="Also judge each diagnosis's quality (groundedness + completeness + actionability) "
             "with the LLM judge. Requires --failure-analysis and GROQ_API_KEY; "
             "adds one judge LLM call per failed test. CLI equivalent of AI_JUDGE_ENABLED=true."
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
    logger.info(f"Log level set to {os.environ['LOG_LEVEL']}, log to file: {os.environ['LOG_TO_FILE']}")

    # For on demand local Poetry run pytest and user can opt-in per run locally without modifying .env
    # AI_ANALYSIS_ENABLED=true from .env is used by Docker compose CI
    if config.getoption('--failure-analysis'):
        os.environ["AI_ANALYSIS_ENABLED"] = "true"
        analyzer.enabled = True # Update instance
        analyzer.api_key = os.getenv("GROQ_API_KEY")    # re-read in case .env loads later
        logger.info(f"AI analysis is enabled. AI_ANALYSIS_ENABLED = {os.environ["AI_ANALYSIS_ENABLED"]}")

    # Same pattern for judging: the flag is CLI sugar for AI_JUDGE_ENABLED=true,
    # which Docker/K8s/CI runs set via .env instead.
    if config.getoption("--judge-diagnosis"):
        os.environ["AI_JUDGE_ENABLED"] = "true"

    if os.getenv("AI_JUDGE_ENABLED", "false").lower() == "true" and not analyzer.enabled:
        logger.warning(
            "--judge-diagnosis/AI_JUDGE_ENABLED has no effect without failure analysis "
            "(--failure-analysis or AI_ANALYSIS_ENABLED=true): there is no diagnosis to judge."
        )

from tests.data.data_loader import load_test_data
from api.movies_api import MoviesAPI
from api.people_api import PeopleAPI
from api.lists_api import ListsAPI
from api.search_api import SearchAPI
from api.discover_api import DiscoverAPI
from api.networks_api import NetworksAPI
from api.trending_api import TrendingAPI
from api.reviews_api import ReviewsAPI

@pytest.fixture(autouse=True)
def _store_test_name(request):
    """
    Auto-use fixture that injects the current test name into class-based test instances.

    Runs automatically before every test. For class-based tests, it sets
    ``_test_name`` on the test instance so helper methods (e.g., FieldAssertions)
    can include the test name in assertion messages and log output.

    Function-based tests are silently skipped (no instance to attach to).

    :param request: Pytest's FixtureRequest object providing test context.

    Example:
        class TestMovies(FieldAssertions):
            def test_get_movie(self, movies_api):
                # self._test_name is automatically set to "test_get_movie"
                ...
    """
    if request.instance is not None:
        request.instance._test_name = request.node.name

@pytest.fixture
def movies_api() -> MoviesAPI:
    """
    Provide a fresh ``MoviesAPI`` client for a test.

    Dedicated, type-annotated alternative to ``get_api_instance('movies_api')``
    — the dependency is declared in the test signature, typo-checked at
    collection time, and gives editor autocomplete for movie endpoints.

    :return: A configured ``MoviesAPI`` instance.
    """
    return MoviesAPI()

@pytest.fixture
def lists_api() -> ListsAPI:
    """
    Provide a fresh ``ListsAPI`` client for a test.

    Dedicated, type-annotated alternative to ``get_api_instance('lists_api')``
    — the dependency is declared in the test signature, typo-checked at
    collection time, and gives editor autocomplete for list endpoints.

    :return: A configured ``ListsAPI`` instance.
    """
    return ListsAPI()

@pytest.fixture
def people_api() -> PeopleAPI:
    """
    Provide a fresh ``PeopleAPI`` client for a test.

    Dedicated, type-annotated alternative to ``get_api_instance('people_api')``
    — the dependency is declared in the test signature, typo-checked at
    collection time, and gives editor autocomplete for people endpoints.

    :return: A configured ``PeopleAPI`` instance.
    """
    return PeopleAPI()

@pytest.fixture
def search_api() -> SearchAPI:
    """
    Provide a fresh ``SearchAPI`` client for a test.

    Dedicated, type-annotated alternative to ``get_api_instance('search_api')``
    — the dependency is declared in the test signature, typo-checked at
    collection time, and gives editor autocomplete for search endpoints.

    :return: A configured ``SearchAPI`` instance.
    """
    return SearchAPI()

@pytest.fixture
def discover_api() -> DiscoverAPI:
    """
    Provide a fresh ``DiscoverAPI`` client for a test.

    Dedicated, type-annotated alternative to ``get_api_instance('discover_api')``
    — the dependency is declared in the test signature, typo-checked at
    collection time, and gives editor autocomplete for discover endpoints.

    :return: A configured ``DiscoverAPI`` instance.
    """
    return DiscoverAPI()

@pytest.fixture
def networks_api() -> NetworksAPI:
    """
    Provide a fresh ``NetworksAPI`` client for a test.

    Dedicated, type-annotated alternative to ``get_api_instance('networks_api')``
    — the dependency is declared in the test signature, typo-checked at
    collection time, and gives editor autocomplete for network endpoints.

    :return: A configured ``NetworksAPI`` instance.
    """
    return NetworksAPI()

@pytest.fixture
def trending_api() -> TrendingAPI:
    """
    Provide a fresh ``TrendingAPI`` client for a test.

    Dedicated, type-annotated alternative to ``get_api_instance('trending_api')``
    — the dependency is declared in the test signature, typo-checked at
    collection time, and gives editor autocomplete for trending endpoints.

    :return: A configured ``TrendingAPI`` instance.
    """
    return TrendingAPI()

@pytest.fixture
def reviews_api() -> ReviewsAPI:
    """
    Provide a fresh ``ReviewsAPI`` client for a test.

    Dedicated, type-annotated alternative to ``get_api_instance('reviews_api')``
    — the dependency is declared in the test signature, typo-checked at
    collection time, and gives editor autocomplete for review endpoints.

    :return: A configured ``ReviewsAPI`` instance.
    """
    return ReviewsAPI()

from tests.schemas.models import (
    GenericResponse, RatingResponse, MovieDetails,
    PopularMoviesResponse, PersonDetails, SearchMoviesResponse,
    DiscoverMoviesResponse, NetworkDetails, TrendingMoviesResponse,
    ReviewDetails
)

@pytest.fixture
def load_schema():
    """
    Fixture that provides a Pydantic model loader for response validation.

    Returns a callable that maps schema names to Pydantic model classes.
    """
    schema_map = {
        'generic_schema': GenericResponse,
        'add_delete_rating_schema': RatingResponse,
        'movie_schema': MovieDetails,
        'popular_movies_schema': PopularMoviesResponse,
        'person_details_schema': PersonDetails,
        'search_movies_schema': SearchMoviesResponse,
        'discover_movies_schema': DiscoverMoviesResponse,
        'network_details_schema': NetworkDetails,
        'trending_movies_schema': TrendingMoviesResponse,
        'review_details_schema': ReviewDetails,
    }

    def _load(name):
        model = schema_map.get(name)
        if model is None:
            raise ValueError(f"Unknown schema: {name}")
        return model
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
    return load_test_data("test_data.yaml")

def pytest_html_report_title(report):
    """
    Customize the title shown in the pytest-html report header.

    :param report: The pytest-html report object.
    """
    report.title = "Movies API Tests Report"

def pytest_html_results_summary(prefix, summary, postfix):
    """
    Customize the results summary section of the pytest-html report.

    Adds a branded header with run timestamp (Eastern Time), a description
    of the test scope, and links to external documentation. Called once
    by pytest-html after all tests have finished.

    :param prefix: List of HTML strings rendered above the pass/fail counts.
    :param summary: List of HTML strings rendered alongside the counts.
    :param postfix: List of HTML strings rendered below the counts.
    """
    # Get current Eastern time
    et_time = datetime.now(ZoneInfo("America/New_York"))

    # Quick status header
    prefix.extend([
        "<h2>🎬 TMDB API Automation Suite</h2>",
        f"<p>Run Date: {et_time.strftime('%Y-%m-%d %H:%M:%S')}</p>"
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

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Capture test failure details and send to AI analyzer.

    Runs after each test phase (setup/call/teardown). On failure during
    the 'call' phase, extracts context from the test and API response,
    then sends it to the LLM for diagnosis. When judging is enabled
    (--judge-diagnosis or AI_JUDGE_ENABLED=true), the diagnosis is scored by an
    LLM judge for groundedness, completeness, and actionability (correctness is
    not scored live — a failure has no reference).
    The diagnosis (and, when judged, the quality verdict) are attached to the
    Allure report as JSON attachments.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    # Build failure context from available information
    failure_context = {
        "test_name": item.name,
        "test_file": str(item.fspath),
        "error_message": str(report.longrepr).split("\n")[-1] if report.longrepr else "",
        "traceback": str(report.longrepr) if report.longrepr else "",
    }

    # Try to extract API response details from the test's local variables
    # (pytest stores them in the call excinfo)
    if call.excinfo:
        # Check if the test had an APIResponse in its locals
        tb = call.excinfo.traceback[-1]
        locals_dict = tb.locals if hasattr(tb, 'locals') else {}
        if 'response' in locals_dict:
            resp = locals_dict['response']
            if hasattr(resp, 'url'):
                failure_context["api_url"] = str(resp.url)
            if hasattr(resp, 'status_code'):
                failure_context["status_code"] = resp.status_code
            if hasattr(resp, 'data'):
                failure_context["response_body"] = resp.data

    diagnosis = analyzer.analyze(failure_context)

    # Attach analysis to Allure report
    if diagnosis:
        confidence = diagnosis.get("confidence", 0)

        if confidence >= 80:
            logger.info(f"🤖 High confidence [{confidence}%] - {diagnosis['root_cause']}")
        elif confidence >= 50:
            logger.warning(f"🤖 Medium confidence [{confidence}%] - {diagnosis['root_cause']}")
        else:
            logger.debug(f"🤖 Low confidence [{confidence}%] - treat with caution: {diagnosis['root_cause']}")

        try:
            import allure
            allure.attach(
                json.dumps(diagnosis, indent=2),
                name="🤖 AI Failure Analysis",
                attachment_type=allure.attachment_type.JSON
            )
        except Exception:
            pass  # Allure not available

        # Judge the diagnosis's quality (groundedness + completeness + actionability,
        # everything except correctness — a live failure has no reference answer).
        # Opt-in and subordinate to analysis: skip unless judging is enabled
        # (--judge-diagnosis sets AI_JUDGE_ENABLED=true in pytest_configure;
        # Docker/K8s/CI set it via .env), so a normal triage run pays for
        # diagnosis but not the extra judge call.
        if os.getenv("AI_JUDGE_ENABLED", "false").lower() == "true":
            from evals.judge import DEFAULT_JUDGE_MODEL, judge_live
            judgement = judge_live(
                failure_context,
                diagnosis,
                model=os.getenv("AI_JUDGE_MODEL", DEFAULT_JUDGE_MODEL),
                api_key=os.getenv("GROQ_API_KEY"),
            )
            if judgement:
                logger.info(
                    f"⚖️ Diagnosis quality [{judgement['overall_verdict']}] — "
                    f"groundedness: {judgement['groundedness']['verdict']}, "
                    f"completeness: {judgement['completeness']['verdict']}, "
                    f"actionability: {judgement['actionability']['verdict']}"
                )
                try:
                    import allure
                    allure.attach(
                        json.dumps(judgement, indent=2),
                        name="⚖️ Diagnosis Quality (LLM-as-a-judge)",
                        attachment_type=allure.attachment_type.JSON
                    )
                except Exception:
                    pass  # Allure not available

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Print all accumulated AI diagnoses as a console section at the end of the run.

    Renders after the built-in summary sections so a terminal-only run gets the
    same triage information as the reports. Keyed off the analyzer's accumulated
    results rather than the --failure-analysis flag, so it also covers analysis
    enabled via AI_ANALYSIS_ENABLED=true in .env; no failures analyzed = no
    section. This is a triage summary (root cause + fix) — the full diagnosis
    (explanation, evidence) stays in the Allure attachment and
    ai_analysis/failure_analysis.json.

    :param terminalreporter: Pytest's ``TerminalReporter`` to write the section to.
    :param exitstatus: Integer exit code of the test session (unused).
    :param config: Pytest's ``Config`` object (unused).
    """
    if not analyzer.results:
        return

    terminalreporter.section(f"🤖 AI Failure Analysis ({len(analyzer.results)} failures)")
    for diagnosis in analyzer.results:
        confidence = diagnosis.get("confidence", 0)
        markup = {"green": True} if confidence >= 80 else {"yellow": True} if confidence >= 50 else {"red": True}
        terminalreporter.write_line(
            f"{diagnosis.get('test_name', 'unknown')}  "
            f"[{diagnosis.get('category', '?')}, confidence {confidence}%]",
            bold=True, **markup,
        )
        terminalreporter.write_line(f"  root cause:    {diagnosis.get('root_cause', 'N/A')}")
        terminalreporter.write_line(f"  suggested fix: {diagnosis.get('suggested_fix', 'N/A')}")
        terminalreporter.write_line("")

def pytest_sessionfinish(session, exitstatus):
    """
    Perform cleanup and metadata writing after all tests complete.

    Fires once at the end of the test session. Handles two tasks:

    - **Allure metadata** (if ``--alluredir`` was passed): copies
      ``tests/allure/categories.json`` into the allure results dir so Allure
      can classify failures, and writes ``environment.properties`` with
      runtime config values (base URL, API version, timeout, log level)
      for the Allure Environment widget, plus GitHub run context
      (event, branch, commit, actor, run number) when running in CI.
    - **AI analysis report**: calls ``analyzer.save_results()`` to write all
      accumulated LLM diagnoses to ``ai_analysis/failure_analysis.json``.

    :param session: The pytest ``Session`` object.
    :param exitstatus: Integer exit code (0 = all passed, 1 = failures, etc.).
    """
    allure_dir = session.config.getoption("--alluredir", default=None)

    if allure_dir:
        # Copy categories.json
        import shutil
        allure_dir = Path(allure_dir)
        categories_file = Path(__file__).parent / "allure" / "categories.json"
        if categories_file.exists():
            shutil.copy(str(categories_file), str(allure_dir / "categories.json"))

        # Write environment.properties with actual runtime config values
        from config.config import Config
        properties = (
            f"Base.URL={Config.BASE_URL}\n"
            f"API.Version={Config.API_VERSION}\n"
            f"Timeout={Config.TIMEOUT}\n"
            f"Log.Level={os.environ.get('LOG_LEVEL', 'INFO')}\n"
            f"Framework=pytest\n"
        )
        # GitHub run context, passed into the container via the CI-generated
        # .env (see .github/workflows/tmdb_test.yml). Absent on local runs.
        if os.environ.get("GITHUB_EVENT_NAME"):
            properties += (
                f"CI.Event={os.environ['GITHUB_EVENT_NAME']}\n"
                f"CI.Branch={os.environ.get('GITHUB_REF_NAME', '')}\n"
                f"CI.Commit={os.environ.get('GITHUB_SHA', '')[:12]}\n"
                f"CI.Actor={os.environ.get('GITHUB_ACTOR', '')}\n"
                f"CI.Run.Number={os.environ.get('GITHUB_RUN_NUMBER', '')}\n"
            )
        (allure_dir / "environment.properties").write_text(properties)

    analyzer.save_results()