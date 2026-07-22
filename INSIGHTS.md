# Insights

Durable, transferable mental models distilled from walking through this
codebase — a place to jog my memory later. Project-*operational* facts (how to
run a thing, this repo's specific conventions) live in the relevant `README.md`
/ `CLAUDE.md`; this file is for concepts that carry beyond one file.

## Performance testing (Locust)

- **Percentiles, not averages.** p50 = typical experience; p95/p99 = the tail
  (slowest 5%/1%). Watch the tail — a healthy p50 with a bad p99 means *some*
  requests choke, and it worsens under load. Averages hide this: ten 10 ms
  requests and one 2000 ms request average to ~191 ms, a value no request saw.
- **Percentiles need volume.** A p99 from 100 requests is ~one data point and
  swings run-to-run. Trust percentiles only from hundreds+ of samples per
  endpoint (a short, few-user run is too thin).
- **User *class* vs *instance*.** `tasks = {SomeTaskSet: 10, ...}` maps classes,
  not instances. Locust builds a **fresh instance per journey run** and discards
  it, so state set on `self` in one journey can't leak into the next, and
  concurrent users never stomp each other. State persists only *within* one
  journey's steps (how page 2 reuses `self.query`), never across journeys/users.
- **`self.interrupt()` ends a `SequentialTaskSet`.** Without it a sequential task
  set loops its own steps forever; `interrupt()` hands control back to the user
  class to schedule a fresh journey.
- **`name=` groups stats rows.** Parametrized URLs (`/movie/603`, `/movie/278`…)
  collapse into one row (`/movie/[id]`) so the table reports per-endpoint, not
  per-id.
- **Load ≈ users ÷ think-time.** With `wait_time = between(1, 3)` (~2 s avg) each
  user does ~0.5 actions/s, so N users ≈ N/2 req/s (10 users ≈ 5 req/s).
- **Cache-busting reveals real latency.** Fixed URLs (`popular?page=1`) get
  served from cache and look artificially fast; rotating random ids
  (`movie/[id]`) measures actual work — hence the details task rotates ids.
- **Omitting the class name spawns all user classes ~50/50** (by user count, not
  request count), mixing different measurement models into one table. Name the
  class you want.

## API layer (`api/base_api.py`)

- **`_build_response` is the single choke-point / adapter.** Every verb funnels
  its raw `requests.Response` through it to produce the standardized
  `APIResponse`. Putting standardization *and* secret-redaction here (not in the
  verbs) means there's exactly one place sanitization can be forgotten — and it
  isn't. Swapping `requests` for another client would touch only this function.
- **Secret redaction, two shapes.** By response time the query is a dict *and*
  baked into the URL string, so masking needs both: `_redact_params` rebuilds
  the dict replacing `_SECRET_QUERY_PARAMS` values with `<hidden>`; `_redact_url`
  regex-substitutes `session_id=…` in the URL, keeping the param *name* (via a
  `\1` backreference) so you still see a secret was sent. Both return copies —
  the real un-redacted values already went to `requests`; only the stored-for-
  humans copy is masked.
- **Comprehension execution order.** A dict/set comprehension reads
  expression-first, loop-last, but *executes* loop-first: the `for` clause drives
  iteration and the head expression is evaluated once per item. Reading rule:
  find the `for` first, then read the leading expression as "what's produced per
  item."