---
name: review-tests
description: >-
  Review changes to this TMDB API testing framework against its own
  conventions and gotchas — the project-specific checks that generic code
  review misses. Use after writing or editing an API client, endpoint method,
  test module, fixture, Pydantic schema, test-data YAML, or assertion helper,
  and before committing/opening a PR. Covers schema dual-registration,
  module-scope test data, the API-client/test separation, response validation
  via Pydantic + assert_http_response, and the known flaky-endpoint exemption.
  Complements (does not replace) the built-in /code-review for generic bugs.
---

# Review test changes

Review the current diff for violations of *this repo's* conventions. These are
the rules generic review can't know — they come from CLAUDE.md and the code.
Run the generic `/code-review` separately for correctness bugs; this skill is
only the convention/gotcha pass.

## Scope

Look at the change under review (`git diff`, `git diff --staged`, or the edits
just made). For each file touched, run the checks below that apply. Verify
every claim against the actual code — open the file, grep for the symbol — do
not assert from memory.

## Checks

### 1. Schema dual-registration (highest-value, easy to miss)
A new or renamed Pydantic model must be registered in **both** places:
- `tests/schemas/models.py` — the model definition.
- the `load_schema` map in `tests/conftest.py` — name → model.

A model present in one but not the other is a bug. Grep both files for the
schema name and confirm it appears in each.

### 2. Module-scope test data
Parametrized test data must be loaded at **module scope**, not inside a
fixture or method:
`TEST_DATA = load_test_data("test_data.yaml", "<section>")` as a module-level
constant. `@pytest.mark.parametrize` runs at collection time, before fixtures
exist, so a fixture-loaded value breaks. Confirm the second arg names a real
top-level YAML section (a wrong/missing section raises `KeyError`), and that
access stays scoped to that section (`TEST_DATA["<section>"][...]`).

### 3. No HTTP logic in tests
Tests must not call `requests`, build URLs, or set headers directly. HTTP
belongs in `api/` — a thin domain method on the relevant endpoint class
(`MoviesAPI`, `PeopleAPI`, `ListsAPI`, `AccountAPI`, `SearchAPI`,
`DiscoverAPI`) that calls
`self.get/post/put/delete` and returns an `APIResponse`. A new endpoint =
a new method on the class (set `_sub_path`), not inline HTTP in a test.

### 4. Assert against APIResponse, never raw requests.Response
Tests assert on the standardized `APIResponse` dataclass (`.data`,
`.status_code`, `.url`, `.elapsed_seconds`, …). Flag any test reaching into a
raw `requests.Response`.

### 5. Validation split: body vs metadata
- **Body** is validated by `load_schema(...).model_validate(response.data)`
  against the strict Pydantic models — the models are the single source of
  truth. Flag duplicated per-field manual body assertions; they belong in the
  model.
- **Metadata** (status, method, content-type, elapsed time, URL) is checked
  with the shared `assert_get_metadata` helper
  (`tests/helpers/response_assertions.py`), which wraps `assert_http_response`.
  Confirm new tests use it rather than ad-hoc status/header asserts or a
  re-introduced per-class `_assert_*_metadata` copy.
- `FieldAssertions.assert_*_field` typed-check methods are legacy — a new test
  calling them is a smell; prefer schema validation.

### 6. Test conventions
- Class-based tests; steps wrapped in `allure.step(...)`; class tagged with
  `@allure.epic/feature/story`.
- New flaky-from-live-data handling: only the documented exemption exists —
  `test_update_list_description` carries `@pytest.mark.flaky(reruns=2,
  reruns_delay=3)` for TMDB-side `update_list` latency. A new `@flaky` /
  raised `exp_max_elp_secs` elsewhere needs a justification in the diff; don't
  let it mask a real regression.

### 7. Contract tests stay in sync
Changes under `tests/contracts/` must keep `@pytest.mark.contract`, point at
the Pact mock (not the live API), validate the mocked body against the **same**
`load_schema` models the integration tests use, and merge into the single
`PACT_CONSUMER`/`PACT_PROVIDER` contract. Flag a contract test that hits the
live API or skips schema validation.

### 8. Sphinx docstrings on everything callable
Every new or edited callable must carry a Sphinx-style docstring — and it is
easy to miss the small ones. Check **all** of these, not just public functions:
- module-level functions and class methods,
- private/underscore helpers (`_build_payload`, `_summarize`, …),
- **nested/inner functions and closures** (e.g. a `verdict()` or `fraction()`
  defined inside another function) — these are the most-often-skipped,
- pytest fixtures and hooks.

A docstring should state what the callable does and document params/returns
with `:param:` / `:returns:` (and `:raises:` where it throws) so Sphinx
autodoc renders it. A one-line summary is fine for a trivial closure. Flag any
callable in the diff with no docstring. Quick sweep: `grep -n "def "` the
changed files and confirm each `def` is followed by a docstring.

### 9. Secrets never logged, printed, or echoed
A credential must never be interpolated into a log line, `print`, exception
message, assertion message, or report attachment. This repo handles real
secrets — `GROQ_API_KEY`, `TMDB_API_KEY`, `TMDB_AUTH_TOKEN` (Bearer),
`TMDB_USER_ACCESS_TOKEN` — and a leak is high-impact: Loguru output goes to the
console, to `logs/test_run.log` under `--log-to-file`, and into CI logs and
Allure/HTML reports, any of which may be retained or shared. INFO is the default
level, so an `logger.info(... {api_key})` leaks on every run.

Flag any line that emits a secret's **value**. Logging whether one is *set* is
fine — log presence, not the secret:
- bad: `logger.info(f"GROQ_API_KEY {self.api_key}")`
- good: `logger.info(f"GROQ_API_KEY {'set' if self.api_key else 'missing'}")`

Also watch for indirect leaks: logging a whole config/`os.environ` dump, an
auth header dict, or a `requests` object that carries the Bearer token. Quick
sweep: grep the changed files for `logger`/`print` lines that mention
`key`, `token`, `secret`, `auth`, `password`, or `Bearer`, and confirm none
interpolate the value. If a secret already reached a shared/CI log, masking
the line forward doesn't unleak it — call out that the credential should be
**rotated**.

### 10. CLAUDE.md drift
If the change adds/removes/renames a client, endpoint, fixture, schema,
helper, command, flag, env var, convention, or gotcha, CLAUDE.md likely needs
updating. Note it and hand off to the `update-claude-md` skill — don't edit
CLAUDE.md inline as part of the review.

## Output

Report findings grouped by file, each as: location → which check it violates →
the fix. If a check passes cleanly, say so briefly rather than listing it.
Don't invent issues to fill the list — a clean diff is a valid result.
