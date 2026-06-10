# mdb_api_layer Project Guidelines

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

**`api/`** — `BaseAPI` (`base_api.py`) owns the `requests.Session`, auth header (Bearer token from `Config`), URL construction (`{base_url}/{api_version}/{endpoint}`), and the four HTTP verbs. Every verb returns a standardized `APIResponse` dataclass (`.data`, `.status_code`, `.url`, `.elapsed_seconds`, etc.) — tests assert against this object, never a raw `requests.Response`. Endpoint classes (`MoviesAPI`, `PeopleAPI`, `ListsAPI`, `AccountAPI`, `SearchAPI`) subclass `BaseAPI`, set a `_sub_path` class attr, and add thin domain methods that call `self.get/post/put/delete`. To add an endpoint: add a method to the relevant class (or a new subclass) — do not put HTTP logic in tests.

**`config/config.py`** — loads `.env`, exposes the `Config` class, and configures Loguru. `configure_logging()` is re-invoked from `pytest_configure` so the CLI log-level flag takes effect before test modules import.

**`tests/conftest.py`** — the wiring hub. Provides:
- Dedicated per-client fixtures — `movies_api`, `people_api`, `lists_api`, `search_api` — each returns a fresh, type-annotated endpoint client (e.g. `MoviesAPI()`); a test declares the one it needs in its signature. (`AccountAPI` has no fixture; it's used directly in `tests/helpers/test_data_generators.py`.)
- `load_schema` fixture: maps a schema name → a **Pydantic model** in `tests/schemas/models.py` (despite the JSON files in `tests/schemas/`, validation is done with `model.model_validate(response.data)`).
- `_store_test_name` (autouse): injects `self._test_name` into class-based tests for assertion messages.
- Hooks for AI failure analysis (`pytest_runtest_makereport`) and Allure/HTML report customization and `environment.properties` writing (`pytest_sessionfinish`).

**Test conventions** — Tests are class-based. Response **bodies** are validated by `load_schema(...).model_validate(response.data)` against the strict Pydantic models in `tests/schemas/models.py` — the models are the single source of truth for body structure/types, so per-field manual assertions are not duplicated in tests. Response **metadata** (status, method, content-type, elapsed time, URL) is checked with the shared `assert_get_metadata` helper (`tests/helpers/response_assertions.py`), which maps a test-case dict onto `assert_http_response`. (Classes still inherit `FieldAssertions` from `tests/helpers/field_assertions.py`, but it now mainly carries `_test_name`; its `assert_*_field` typed-check methods are no longer called by any test.) Tests are data-driven: `TEST_DATA = load_test_data("test_data.yaml", "<section>")` is a **module-level constant** (required because `@pytest.mark.parametrize` is evaluated at collection time, before fixtures exist). The second arg scopes the load to one top-level YAML section (e.g. `"get_movie_details"`), so only that section's `$placeholder` generators run — access stays `TEST_DATA["<section>"][...]`. `data_loader.py` applies YAML defaults (a section's `defaults` override the global `defaults` block for shared keys) and resolves `$placeholder` tokens to generator functions (random rating, random movie id, timestamp, etc.); `$random_movie_id` reads `movie_ids.txt`, which is cached per process via `lru_cache`. Tests wrap steps in `allure.step(...)` and tag with `@allure.epic/feature/story`.

**`tests/contracts/`** — Pact consumer-driven contract tests, marked `@pytest.mark.contract`. They point a client at a local Pact mock server (no live API) and emit a single merged `mdb_api_layer-api_pvd.json` contract into `tests/pacts/`. Shared Pact wiring lives in `tests/contracts/conftest.py`: the `pact` fixture (one consumer/provider pair — `PACT_CONSUMER`/`PACT_PROVIDER` — so all interactions merge into one contract file), `pact_movies_api` (client whose `base_url` each test repoints at the mock once `pact.serve()` is up), and `pact_address` (host + OS-assigned port). Each test's mocked response body is also validated against the same `load_schema` Pydantic models the integration tests use, keeping contract and integration in sync.

**`failure_mcp/`** — an MCP server (`server.py`, stdio transport) that wraps the existing `FailureAnalyzer` singleton (`tests/helpers/failure_analyzer.py`) and exposes `analyze_failure`, `get_results`, `save_results` as tools. It does not modify the analyzer. Run with `poetry run python -m failure_mcp.server` (needs `AI_ANALYSIS_ENABLED=true` + `GROQ_API_KEY`).

## Gotchas

- The framework hits the live TMDB API; tests can fail due to stale data (deleted movies, expired tokens) rather than code bugs — that's what the AI failure analysis classifies.
- The v4 list-write endpoint (`update_list`) is intermittently very slow (occasional 19s+ responses, sometimes a 30s `ReadTimeout`). `test_update_list_description` carries `@pytest.mark.flaky(reruns=2, reruns_delay=3)` (pytest-rerunfailures) to absorb these transient latency/timeout flakes, and `update_list.defaults.valid.exp_max_elp_secs` is raised to 15. These are TMDB-side, not code regressions.
- When adding a new Pydantic schema, register it in **both** `tests/schemas/models.py` and the `load_schema` map in `conftest.py`.
- Boolean **query params** in `test_data.yaml` must be quoted strings (`"include_adult": "true"`), not YAML booleans — `requests` serializes Python bools as `True`/`False` in the URL, which TMDB only tolerates undocumented. JSON **body** payloads (e.g. `update_list`'s `public`) correctly use real booleans.
- New parametrized test data must go through `load_test_data` at module scope, not inside a fixture. Pass the module's top-level YAML section name as the second arg (`load_test_data("test_data.yaml", "<section>")`); a wrong/missing section raises `KeyError` listing the valid ones.

## Working style
- State assumptions; if multiple interpretations exist, ask rather than pick silently.
- Minimum code that solves the problem - no speculative abstractions or config.
- Surgical edits: match existing style, touch only what the request requires, clean up only the orphans your change creates.
- Define a verifiable success check before coding; for test work that usually means a failing test that your change makes pass.
- If you notice unrelated dead code, mention it - don't delete it unless asked.
- For multistep tasks, state a brief plan:
    ```
    1. [Step] → verify: [check]
    2. [Step] → verify: [check]
    3. [Step] → verify: [check]
    ```