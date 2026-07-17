# Performance testing with Locust

Load tests for the TMDB movies endpoints, separate from the pytest suite in `tests/`
(pytest never collects this directory). Locust spawns simulated users that run the
weighted tasks in `locustfile.py` and records latency/throughput/failure stats per
endpoint.

## How it works

Locust spawns simulated users (`-u` total, ramped at `-r` users/sec) and runs them
for the duration `-t`. Each user lives in its own greenlet with its own `requests`
session, carrying the same `.env`-sourced Bearer auth the test suite uses
(`config.config.Config`), and pauses 1–3 s of think-time between actions so the
load stays realistic. Every request is recorded into per-endpoint stats — request
count, failures, median/p95/p99 latency, req/s — with parametrized URLs grouped
under one stats row via `name=` (e.g. `/3/movie/[id]` instead of thousands of
distinct ids). A journey's later steps reuse ids taken from earlier responses, so
the traffic is correlated like a real client's rather than independent samples.

## User models

`locustfile.py` defines two user classes — pass the class name on the CLI to pick one
(no class name spawns both 50/50):

- **`MoviesUser`** — endpoint traffic mix: each iteration fires one independent,
  weighted read-only request (details ×3, popular ×2, top-rated ×1, alt titles ×1).
  Best for per-endpoint latency baselining.
- **`JourneyUser`** — realistic sessions: each iteration runs one complete
  `SequentialTaskSet` journey, picked by weight, with think-time between steps
  and ids chained from earlier responses.

**User journeys covered by `JourneyUser`** (picked per iteration by a
~50/25/15/10 mix):

| Journey | Flow |
|---|---|
| Browse & drill down (50%) | popular list → details of a listed movie → its alternative titles |
| Search-driven (25%) | search a rotating query (shared with the integration suite's `test_data.yaml`) → page 2 of the same query → details of a result |
| Filtered discovery (15%) | genre/sort-filtered discover → pages 2–3 → details of a hit |
| Cast exploration (10%) | movie details → its credits → a cast member's person details |

Write endpoints (ratings, lists) are deliberately excluded from both models.

> **Live-API warning:** these tests hit the real TMDB API with your token.
> Keep user counts low (≤ 5 users ≈ 2–3 req/s with the configured think-time).
> This setup is for latency baselining and learning Locust — not stress testing
> a third-party service you don't own.

## Prerequisites

`.env` with a valid `TMDB_AUTH_TOKEN` (same as the test suite), dependencies via
`poetry install`.

## Running

```bash
# Interactive web UI (pick user count / spawn rate, live charts) → http://localhost:8089
poetry run locust -f performance/locustfile.py MoviesUser

# Headless smoke run: 3 users, spawning 1/s, for 30 seconds
poetry run locust -f performance/locustfile.py MoviesUser --headless -u 3 -r 1 -t 30s

# Journey-based run (realistic sessions instead of independent requests)
poetry run locust -f performance/locustfile.py JourneyUser --headless -u 5 -r 2 -t 2m

# Longer baseline with an HTML report (gitignored)
poetry run locust -f performance/locustfile.py MoviesUser --headless -u 3 -r 1 -t 2m --html performance/report.html

# CSV stats for diffing between runs (writes performance/baseline_*.csv, gitignored)
poetry run locust -f performance/locustfile.py MoviesUser --headless -u 3 -r 1 -t 2m --csv performance/baseline
```

## Reading the output

Each row in the stats table is one logical endpoint (parametrized URLs are grouped
via `name=`, e.g. `/3/movie/[id]`):

- **# reqs / # fails** — request count and failures (non-2xx, or a `catch_response`
  block calling `response.failure(...)`).
- **Avg / Min / Max** — response time in ms. Averages hide spikes; prefer percentiles.
- **Med / 95% / 99%** — percentiles. p95/p99 are the numbers to watch: "95/99% of
  requests were at least this fast." A healthy p50 with a bad p99 means tail latency.
- **req/s** — throughput actually achieved.

A run "passes" when failures stay at 0 and percentiles stay near your baseline;
compare CSV exports between runs to spot regressions.