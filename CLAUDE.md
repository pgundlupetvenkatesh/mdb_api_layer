# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A pytest-based API testing framework for The Movie Database (TMDB) REST API. It is a test suite, not an application — 
there is no server to run. Work consists of writing/maintaining API client wrappers and the tests that exercise them.

## Commands

Dependencies are managed with Poetry; always run through `poetry run`.

```bash
poetry install                                          # set up venv from poetry.lock
poetry run pytest tests/ --failure-analysis -v                            # all tests (integration + contract)
poetry run pytest tests/ --failure-analysis -v -m "not contract"          # integration only
poetry run pytest tests/contracts/ --failure-analysis -v -m contract      # contract (Pact) tests only
poetry run pytest tests/movies/test_details.py --failure-analysis -v -s   # one module
poetry run pytest tests/movies/test_details.py::TestDetails::test_get_movie_details --failure-analysis -v -s   # one test
```

Test-run flags (all defined in `tests/conftest.py` via `pytest_addoption`):
- `--loguru-log-level=DEBUG|INFO|WARNING|ERROR|CRITICAL` — app log verbosity (default INFO)
- `--log-to-file` — also write to `logs/test_run.log`
- `--failure-analysis` — opt into AI failure analysis for that run (needs `GROQ_API_KEY`)

Reporting:
```bash
poetry run pytest tests/ --failure-analysis --html=report/tmdb_report.html --self-contained-html -v   # HTML
poetry run pytest tests/ --failure-analysis --alluredir=allure-results -v && allure serve allure-results   # Allure (brew install allure)
```

Docs (Sphinx, from docstrings): `cd docs && make clean && make html` → open `docs/_build/html/index.html`.

Docker (parallel integration + contract containers, reads `.env`): `docker compose up --build`.

## Configuration

All runtime config comes from environment variables loaded from `.env` (gitignored) via `config/config.py`. `TMDB_API_KEY` and `TMDB_AUTH_TOKEN` (Bearer, v4) are required; everything else has defaults in the `Config` class. Tests will hit the live TMDB API unless run against the Pact mock (contract tests only).

## Architecture

Layered, with a strict separation between the API client and the tests:

**`api/`** — `BaseAPI` (`base_api.py`) owns the `requests.Session`, auth header (Bearer token from `Config`), URL construction (`{base_url}/{api_version}/{endpoint}`), and the four HTTP verbs. Every verb returns a standardized `APIResponse` dataclass (`.data`, `.status_code`, `.url`, `.elapsed_seconds`, etc.) — tests assert against this object, never a raw `requests.Response`. Endpoint classes (`MoviesAPI`, `PeopleAPI`, `ListsAPI`, `AccountAPI`) subclass `BaseAPI`, set a `_sub_path` class attr, and add thin domain methods that call `self.get/post/put/delete`. To add an endpoint: add a method to the relevant class (or a new subclass) — do not put HTTP logic in tests.

**`config/config.py`** — loads `.env`, exposes the `Config` class, and configures Loguru. `configure_logging()` is re-invoked from `pytest_configure` so the CLI log-level flag takes effect before test modules import.

**`tests/conftest.py`** — the wiring hub. Provides:
- `get_api_instance` fixture: a *factory* — call `get_api_instance('movies_api')` to get a client. The string→class map lives in the fixture.
- `load_schema` fixture: maps a schema name → a **Pydantic model** in `tests/schemas/models.py` (despite the JSON files in `tests/schemas/`, validation is done with `model.model_validate(response.data)`).
- `_store_test_name` (autouse): injects `self._test_name` into class-based tests for assertion messages.
- Hooks for AI failure analysis (`pytest_runtest_makereport`) and Allure/HTML report customization and `environment.properties` writing (`pytest_sessionfinish`).

**Test conventions** — Tests are class-based, inherit `FieldAssertions` (mixin in `tests/helpers/field_assertions.py`) for typed field checks, and use `assert_http_response` (`tests/helpers/response_assertions.py`) for response metadata. They are data-driven: `TEST_DATA = load_test_data("test_data.yaml")` is a **module-level constant** (required because `@pytest.mark.parametrize` is evaluated at collection time, before fixtures exist). `data_loader.py` applies YAML defaults and resolves `$placeholder` tokens to generator functions (random rating, random movie id, timestamp, etc.). Tests wrap steps in `allure.step(...)` and tag with `@allure.epic/feature/story`.

**`tests/contracts/`** — Pact consumer-driven contract tests, marked `@pytest.mark.contract`. They point a client at a local Pact mock server (no live API) and emit `.json` contracts into `tests/pacts/`.

**`failure_mcp/`** — an MCP server (`server.py`, stdio transport) that wraps the existing `FailureAnalyzer` singleton (`tests/helpers/failure_analyzer.py`) and exposes `analyze_failure`, `get_results`, `save_results` as tools. It does not modify the analyzer. Run with `poetry run python -m failure_mcp.server` (needs `AI_ANALYSIS_ENABLED=true` + `GROQ_API_KEY`).

## Gotchas

- The framework hits the live TMDB API; tests can fail due to stale data (deleted movies, expired tokens) rather than code bugs — that's what the AI failure analysis classifies.
- When adding a new Pydantic schema, register it in **both** `tests/schemas/models.py` and the `load_schema` map in `conftest.py`.
- New parametrized test data must go through `load_test_data` at module scope, not inside a fixture.
