# mdb_api_layer Project Guidelines

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A pytest-based API testing framework for The Movie Database (TMDB) REST API. It is a test suite, not an application — 
there is no server to run. Work consists of writing/maintaining API client wrappers and the tests that exercise them.

## Commands

Dependencies are managed with Poetry; always run through `poetry run`.

```bash
poetry install                                          # set up venv from poetry.lock
poetry run pytest tests/ --failure-analysis -v                            # TMDB API suite (integration + contract); unit excluded by default via addopts
poetry run pytest tests/ --failure-analysis -v -m "not contract and not unit"   # live TMDB integration only
poetry run pytest tests/contracts/ --failure-analysis -v -m contract      # contract (Pact) tests only
poetry run pytest tests/ -v -m unit                                       # offline unit tests only (opt-in; no API/GROQ_API_KEY)
poetry run pytest tests/movies/test_details.py --failure-analysis -v -s   # one module
poetry run pytest tests/movies/test_details.py::TestDetails::test_get_movie_details --failure-analysis -v -s   # one test
```

Test-run flags (all defined in `tests/conftest.py` via `pytest_addoption`):
- `--loguru-log-level=DEBUG|INFO|WARNING|ERROR|CRITICAL` — app log verbosity (default INFO)
- `--log-to-file` — also write to `logs/test_run.log`
- `--failure-analysis` — opt into AI failure analysis for that run (needs `GROQ_API_KEY`)
- `--judge-diagnosis` — also score each diagnosis's groundedness + completeness + actionability with the LLM judge (needs `--failure-analysis`; adds one judge call per failed test). CLI equivalent of `AI_JUDGE_ENABLED=true`, which is how Docker/K8s/CI enable it (in GitHub Actions via the `AI_JUDGE_ENABLED` repo variable) — mirroring the `--failure-analysis` ↔ `AI_ANALYSIS_ENABLED` pair

Reporting:
```bash
poetry run pytest tests/ --failure-analysis --html=report/tmdb_report.html --self-contained-html -v   # HTML
poetry run pytest tests/ --failure-analysis --alluredir=allure-results -v && allure serve allure-results   # Allure (brew install allure)
```

Evaluate the AI analyzer (LLM-as-a-judge over a golden dataset; needs `GROQ_API_KEY`): `poetry run python -m evals` (override the judge with `--judge-model <groq-model-id>`).

Docs (Sphinx, from docstrings): `cd docs && make clean && make html` → open `docs/_build/html/index.html`.

Performance (Locust, hits live TMDB — keep load gentle, ≤5 users): `poetry run locust -f performance/locustfile.py <MoviesUser|JourneyUser>` (web UI at `:8089`) or add `--headless -u 3 -r 1 -t 30s`; add `--html`/`--csv performance/<name>` for reports (gitignored). Omitting the class name spawns both user classes 50/50. See `performance/README.md`.

Docker (parallel integration + contract containers, reads `.env`): `docker compose up --build`.

CI (`.github/workflows/tmdb_test.yml`) runs the Docker suite on push/PR to main, nightly at 09:17 UTC (`schedule` cron, ~2 AM Pacific), and on manual `workflow_dispatch`; the HTML/Allure reports publish to GitHub Pages on every non-PR run.

## Configuration

All runtime config comes from environment variables loaded from `.env` (gitignored) via `config/config.py`; `.env.example` is the committed template (`cp .env.example .env`, fill in credentials) — when adding an env var, add it there too. `TMDB_API_KEY` and `TMDB_AUTH_TOKEN` (Bearer, v4) are required; everything else has defaults in the `Config` class. Tests will hit the live TMDB API unless run against the Pact mock (contract tests only).

## Architecture

Layered, with a strict separation between the API client and the tests:

**`api/`** — `BaseAPI` (`base_api.py`) owns the `requests.Session`, auth header (Bearer token from `Config`), URL construction (`{base_url}/{api_version}/{endpoint}`), and the four HTTP verbs. Every verb returns a standardized `APIResponse` dataclass (`.data`, `.status_code`, `.url`, `.elapsed_seconds`, etc.) — tests assert against this object, never a raw `requests.Response`. Secret query params (`_SECRET_QUERY_PARAMS`, currently `session_id`) are masked to `<hidden>` in `APIResponse.url`/`.request_params`, so responses are safe to log or attach to reports — and a test must never assert on a raw credential value there. Endpoint classes (`MoviesAPI`, `PeopleAPI`, `ListsAPI`, `AccountAPI`, `SearchAPI`, `DiscoverAPI`, `NetworksAPI`) subclass `BaseAPI`, set a `_sub_path` class attr, and add thin domain methods that call `self.get/post/put/delete`. To add an endpoint: add a method to the relevant class (or a new subclass) — do not put HTTP logic in tests.

**`config/config.py`** — loads `.env`, exposes the `Config` class, and configures Loguru. `configure_logging()` is re-invoked from `pytest_configure` so the CLI log-level flag takes effect before test modules import.

**`tests/conftest.py`** — the wiring hub. Provides:
- Dedicated per-client fixtures — `movies_api`, `people_api`, `lists_api`, `search_api`, `discover_api`, `networks_api` — each returns a fresh, type-annotated endpoint client (e.g. `MoviesAPI()`); a test declares the one it needs in its signature. (`AccountAPI` has no fixture; it's used directly in `tests/helpers/test_data_generators.py`.)
- `load_schema` fixture: maps a schema name → a **Pydantic model** in `tests/schemas/models.py`; validation is `model.model_validate(response.data)`.
- `_store_test_name` (autouse): injects `self._test_name` into class-based tests for assertion messages.
- Hooks: when `--failure-analysis` is on, `pytest_runtest_makereport` diagnoses each failure and attaches it to Allure; adding `--judge-diagnosis` (or `AI_JUDGE_ENABLED=true`) also scores each diagnosis via `evals.judge.judge_live` (judge model overridable with `AI_JUDGE_MODEL`). `pytest_sessionfinish` handles Allure/HTML report customization and `environment.properties`. `pytest_terminal_summary` re-prints all accumulated diagnoses as an end-of-run console section (also fires under `AI_ANALYSIS_ENABLED=true`; silent when nothing was analyzed).

**Test conventions** — Tests are class-based. Response **bodies** are validated by `load_schema(...).model_validate(response.data)` against the strict Pydantic models in `tests/schemas/models.py` — the models are the single source of truth for body structure/types, so per-field manual assertions are not duplicated in tests. Response **metadata** (status, method, content-type, elapsed time, URL) is checked with the shared `assert_get_metadata` helper (`tests/helpers/response_assertions.py`), which maps a test-case dict onto `assert_http_response`. (Classes still inherit `FieldAssertions` from `tests/helpers/field_assertions.py`, but it now mainly carries `_test_name`; its `assert_*_field` typed-check methods are no longer called by any test.) Tests are data-driven: `TEST_DATA = load_test_data("test_data.yaml", "<section>")` is a **module-level constant** (required because `@pytest.mark.parametrize` is evaluated at collection time, before fixtures exist). The second arg scopes the load to one top-level YAML section (e.g. `"get_movie_details"`), so only that section's `$placeholder` generators run — access stays `TEST_DATA["<section>"][...]`. `data_loader.py` applies YAML defaults (a section's `defaults` override the global `defaults` block for shared keys) and resolves `$placeholder` tokens to generator functions (random rating, random movie id, timestamp, etc.); `$random_movie_id` reads `movie_ids.txt`, which is cached per process via `lru_cache`. Tests wrap steps in `allure.step(...)` and tag with `@allure.epic/feature/story`.

**`tests/contracts/`** — Pact consumer-driven contract tests, marked `@pytest.mark.contract`. They point a client at a local Pact mock server (no live API) and emit a single merged `mdb_api_layer-api_pvd.json` contract into `tests/pacts/`. Shared Pact wiring lives in `tests/contracts/conftest.py`: the `pact` fixture (one consumer/provider pair — `PACT_CONSUMER`/`PACT_PROVIDER` — so all interactions merge into one contract file), `pact_movies_api` (client whose `base_url` each test repoints at the mock once `pact.serve()` is up), and `pact_address` (host + OS-assigned port). Each test's mocked response body is also validated against the same `load_schema` Pydantic models the integration tests use, keeping contract and integration in sync.

**`tests/journeys/`** (allure feature `Journeys`) — multi-endpoint integration tests that chain live calls the way `JourneyUser` does in perf: one test declares several client fixtures, drills an id out of one response, feeds it into the next, and asserts the chain resolves (e.g. `test_search_to_details.py` searches `search/movie` then opens `movie/{id}` for the top result). Each step still validates with the same `assert_get_metadata` + `load_schema` helpers; seed queries are reused from `test_data.yaml`'s `search_movies` section, not a new YAML block. No marker — these run in the default live suite (and hit ≥2 endpoints, so are marginally flakier).

**`failure_mcp/`** — an MCP server (`server.py`, stdio transport) that wraps the existing `FailureAnalyzer` singleton (`tests/helpers/failure_analyzer.py`) and exposes `analyze_failure`, `get_results`, `save_results` as tools. It does not modify the analyzer. Run with `poetry run python -m failure_mcp.server` (needs `AI_ANALYSIS_ENABLED=true` + `GROQ_API_KEY`).

**`evals/`** — LLM-as-a-judge for the failure analyzer's diagnosis quality. `evals/judge.py` is the shared judge (Groq, `openai/gpt-oss-120b` by default — a different model family from the analyzer, so no self-preference): `judge_case` scores correctness + groundedness + completeness + actionability for the offline eval; `judge_live` scores everything except correctness for the live in-pytest path (wired into `pytest_runtest_makereport`, see above). The offline eval is a standalone CLI (`python -m evals`): it runs a fresh force-enabled `FailureAnalyzer` (never touches the module singleton) over `evals/golden_dataset.yaml` (≥1 case per failure category, each with an `expected` reference block) and writes a per-case + aggregate JSON report to `evals/results/` (gitignored). Reuses the existing `groq` dep and `GROQ_API_KEY`. The package's pure logic is unit-tested in `tests/evals/`, marked `@pytest.mark.unit` — the suite's only offline tests, excluded from the default run by `addopts = "-m 'not unit'"`; opt in with `-m unit`.

**`performance/`** — Locust load tests (`locustfile.py`), outside pytest collection (`testpaths = ["tests"]`). Two user classes, picked by class name on the CLI: `MoviesUser` (endpoint traffic mix — weighted, independent read-only GETs mirroring `MoviesAPI`) and `JourneyUser` (four `SequentialTaskSet` journeys — browse & drill down, search-driven, filtered discovery, cast exploration — weighted ~50/25/15/10, with later steps chaining ids from earlier responses; search queries come from `test_data.yaml`'s `search_movies` section via `load_test_data`). All requests go through Locust's instrumented `self.client` — not `BaseAPI`, which would bypass the stats. Auth/base URL come from `Config`; random ids reuse `pick_random_movie_id` from `tests/helpers/test_data_generators.py`. Parametrized URLs are grouped in the stats table via `name=` (e.g. `/3/movie/[id]`); write endpoints are excluded from both models.

## Gotchas

- The framework hits the live TMDB API; tests can fail due to stale data (deleted movies, expired tokens) rather than code bugs — that's what the AI failure analysis classifies.
- The v4 list-write endpoint (`update_list`) is intermittently very slow (occasional 19s+ responses, sometimes a 30s `ReadTimeout`). `test_update_list_description` carries `@pytest.mark.flaky(reruns=2, reruns_delay=3)` (pytest-rerunfailures) to absorb these transient latency/timeout flakes, and `update_list.defaults.valid.exp_max_elp_secs` is raised to 15. These are TMDB-side, not code regressions.
- When adding a new Pydantic schema, register it in **both** `tests/schemas/models.py` and the `load_schema` map in `conftest.py`.
- Sphinx does **not** auto-discover modules: the `automodule` lists in `docs/*.rst` are hand-maintained (`api.rst` for clients, `tests.rst` for test modules). When adding a new module, add its entry to the matching `.rst` and rebuild (`cd docs && make clean && make html`) before committing.
- Boolean **query params** in `test_data.yaml` must be quoted strings (`"include_adult": "true"`), not YAML booleans — `requests` serializes Python bools as `True`/`False` in the URL, which TMDB only tolerates undocumented. JSON **body** payloads (e.g. `update_list`'s `public`) correctly use real booleans.
- New parametrized test data must go through `load_test_data` at module scope, not inside a fixture. Pass the module's top-level YAML section name as the second arg (`load_test_data("test_data.yaml", "<section>")`); a wrong/missing section raises `KeyError` listing the valid ones.

## Working style
- State assumptions; if multiple interpretations exist, ask rather than pick silently.
- Minimum code that solves the problem - no speculative abstractions or config.
- Surgical edits: match existing style, touch only what the request requires, clean up only the orphans your change creates.
- Define a verifiable success check before coding; for test work that usually means a failing test that your change makes pass.
- If you notice unrelated dead code, mention it - don't delete it unless asked.
- Commits are atomic: one logical change per commit, each leaving the repo working (full rules in `.claude/skills/commit-rules/`).
- Merged branches don't linger: GitHub auto-deletes the remote branch on PR merge (`delete_branch_on_merge` repo setting); delete the local branch after its PR merges.
- For multistep tasks, state a brief plan:
    ```
    1. [Step] → verify: [check]
    2. [Step] → verify: [check]
    3. [Step] → verify: [check]
    ```