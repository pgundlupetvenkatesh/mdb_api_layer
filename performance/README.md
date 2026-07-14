# Performance testing with Locust

Load tests for the TMDB movies endpoints, separate from the pytest suite in `tests/`
(pytest never collects this directory). Locust spawns simulated users that run the
weighted tasks in `locustfile.py` and records latency/throughput/failure stats per
endpoint.

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
poetry run locust -f performance/locustfile.py

# Headless smoke run: 3 users, spawning 1/s, for 30 seconds
poetry run locust -f performance/locustfile.py --headless -u 3 -r 1 -t 30s

# Longer baseline with an HTML report (gitignored)
poetry run locust -f performance/locustfile.py --headless -u 3 -r 1 -t 2m --html performance/report.html

# CSV stats for diffing between runs (writes performance/baseline_*.csv, gitignored)
poetry run locust -f performance/locustfile.py --headless -u 3 -r 1 -t 2m --csv performance/baseline
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