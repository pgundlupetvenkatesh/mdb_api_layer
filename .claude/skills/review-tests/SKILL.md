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
(`MoviesAPI`, `PeopleAPI`, `ListsAPI`, `AccountAPI`) that calls
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

### 8. CLAUDE.md drift
If the change adds/removes/renames a client, endpoint, fixture, schema,
helper, command, flag, env var, convention, or gotcha, CLAUDE.md likely needs
updating. Note it and hand off to the `update-claude-md` skill — don't edit
CLAUDE.md inline as part of the review.

## Output

Report findings grouped by file, each as: location → which check it violates →
the fix. If a check passes cleanly, say so briefly rather than listing it.
Don't invent issues to fill the list — a clean diff is a valid result.
