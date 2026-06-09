---
name: update-claude-md
description: >-
  Update CLAUDE.md so it stays accurate after a significant change to this TMDB
  API testing framework. Use after adding/removing/renaming an API client,
  endpoint method, test module, fixture, schema, or helper; changing how tests
  are run (Poetry/pytest commands, flags, markers); adding/changing config or
  env vars; introducing a new convention, gotcha, or dependency; or reworking
  Docker/K8s/CI/MCP wiring. Trigger when finishing such a change, before
  committing, or when the user asks to "update CLAUDE.md" / "keep the docs in
  sync". Skip for pure test-data tweaks, formatting, or one-off fixes that don't
  change structure, commands, conventions, or gotchas.
---

# Keep CLAUDE.md in sync

CLAUDE.md is the single onboarding doc for this repo (see its own sections:
What this is, Commands, Configuration, Architecture, Gotchas). It must keep
matching the actual code. After a significant change, reconcile it.

## What counts as "significant"

Update CLAUDE.md when a change touches any of these:

- **Commands** — new/changed Poetry or pytest invocation, CLI flag
  (`pytest_addoption` in `tests/conftest.py`), marker, report command, Docker
  or K8s command.
- **Configuration** — new/removed/renamed env var, a changed default in the
  `Config` class, a new required credential.
- **Architecture** — new or removed API client / endpoint method, fixture,
  Pydantic schema, helper module, or a change to how layers connect
  (`api/`, `config/`, `tests/conftest.py`, `tests/contracts/`, `failure_mcp/`).
- **Conventions** — a new pattern tests must follow (validation, data-driven
  loading, allure tagging, assertion helpers).
- **Gotchas** — a new flaky endpoint, a registration that must happen in two
  places, a non-obvious failure mode.
- **Dependencies** — a package added/removed that changes how the project is
  set up or run.

Skip it for: test-data value tweaks, formatting/lint-only diffs, comment
changes, and one-off bug fixes that don't alter structure, commands,
conventions, or gotchas.

## Procedure

1. **See what changed.** Review the diff (`git diff`, `git diff --staged`, or
   the change you just made). Identify which of the categories above it hits.
2. **Find the matching section** in CLAUDE.md (Commands / Configuration /
   Architecture / Gotchas). Edit in place — don't append a duplicate or a
   changelog. There is exactly one home for each fact.
3. **Verify against the code, not memory.** Before writing a claim, confirm it:
   open the file, grep for the symbol, check the env var is read in
   `config/config.py`, the flag is in `pytest_addoption`, the schema is in
   *both* `tests/schemas/models.py` and the `load_schema` map in
   `conftest.py`, etc. Never document something you haven't confirmed exists.
4. **Match the existing voice.** CLAUDE.md is terse, declarative, and
   high-signal — file paths in backticks, no marketing, no step-by-step
   tutorials. Add the minimum that makes the doc correct again; prefer editing
   a sentence over adding a paragraph. Remove lines that the change made false.
5. **Re-read the touched section once** to confirm it now matches reality and
   reads consistently with the rest.

## Notes

- CLAUDE.md and README.md serve different audiences: CLAUDE.md is the concise
  agent/onboarding brief; README.md is the full human walkthrough. A change can
  require updating one, the other, or both — judge per change; don't mirror
  content between them.
- If a change makes an existing gotcha obsolete, delete it rather than leaving
  a stale warning.
- Keep the edit in the same commit/PR as the change it documents so the doc and
  the code never drift.
