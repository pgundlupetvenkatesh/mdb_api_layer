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

## Python & pytest

- **A lambda body must be a single *expression*.** Statements (notably assignment
  `=`) aren't expressions, so `lambda c: c["k"] = v` is a **syntax error**. Work
  around it with the dunder the sugar maps to: `d[k] = v` is
  `d.__setitem__(k, v)`, and a method call *is* an expression — legal in a lambda.
- **Lambdas as parametrize data.** A row like `(lambda c: c.pop("id"), "missing 'id'")`
  stores *"how to break the case"* + *"the error it should raise"* as data. The
  test calls `mutate(case)`; the lambda's **return value is discarded** — it works
  by side effect, because dicts are mutable and passed by reference, so mutating
  the arg changes the caller's object. Two different mutations can hit the same
  error via different code paths (e.g. removing a nested key vs. removing its whole
  parent block).

- **A model *factory* shares a body while keeping distinct model names.** When
  several Pydantic models share one field layout but must stay separately named
  (e.g. `tests/schemas/models.py`'s paginated list responses — one per endpoint
  for `load_schema` registration and endpoint-specific validation-error names),
  a `def paginated_movie_list(ge=1): return create_model("PaginatedMovieList",
  page=(StrictInt, Field(ge=ge)), ...)` factory returns a *fresh base class* per
  call, and each endpoint does `class SearchMoviesResponse(paginated_movie_list())`.
  A function (not a plain base class) is what lets one axis vary — here the `ge`
  bound (popular passes `ge=0`, the rest default to `1`) — without duplicating the
  field list. `create_model(name, field=(type, Field(...)))` is the programmatic
  equivalent of a `class` body; the leaf class name wins, so the shared
  `"PaginatedMovieList"` base name only ever appears in the Method Resolution Order(MRO).

## Claude Code tooling

- **The three review commands target different things.** `/review <PR>` reviews a
  **remote GitHub PR** (fetches via `gh`, posts inline comments back) — for
  someone else's PR or one already pushed. `/code-review` reviews the **local
  working diff**, prints to terminal (`--comment` posts to a PR, `--fix` applies
  fixes) — for pre-push self-review. `/review-tests` is this repo's
  **project-convention** pass on local changes. Built-in command prompts are
  compiled into the binary, not on-disk files.

## Design principles

- **Each response attribute is checked exactly once, by the layer that owns it.**
  Three layers with non-overlapping jobs: `assert_get_metadata` checks the HTTP
  envelope (status/method/content-type/elapsed/url); a strict Pydantic model
  (`model_validate`, `extra="forbid"`) checks the *entire* body's shape, types,
  and field constraints; and the test itself asserts only what neither can — that
  the returned resource is *the one requested* (`res_body['id'] == requested_id`,
  a request/response **correlation** check). Re-asserting individual body fields
  in the test would just duplicate the schema. Corollary: when the lookup key is
  **randomly generated** (e.g. a review id harvested live), the id echo is the
  *only* value assertion possible — the test can't know the author/content ahead
  of time, so there's nothing else concrete to compare against without hardcoding.
- **Separate "run the feature" from "evaluate the feature."** If a feature call
  and a meta-evaluation call are bundled behind one switch, the common case
  (just run it) silently pays for the rare case (grade it) — cost that scales with
  usage, plus log/report noise. Give evaluation its own flag, kept *subordinate*
  (it does nothing without the feature flag). Example here: `--failure-analysis`
  vs. the judge switch.
- **Freeze the input to isolate the variable.** When tuning one non-deterministic
  stage (e.g. an LLM judge prompt), re-running the *upstream* non-deterministic
  stage each time adds a confound — you can't tell if the output changed because
  of your edit or upstream noise. Caching/reusing the upstream output (what
  `--reuse-diagnoses` did) freezes it so you measure only what you changed. Trade-
  off: frozen inputs aren't honest *end-to-end* numbers — use a fresh full pass
  for those.

## LLM confidence & token economy

> The five AI quality gates themselves (what each enforces + how to enable them) are
> enumerated in [`README.md`](README.md#ai-quality-gates). This section is the *why*.

- **Self-reported confidence is not verification.** A number the diagnosis model
  emits about its own answer (the analyzer's `confidence` field) comes from the
  *same* model that wrote the answer — it's self-assessment, not an independent
  check. Verbalized self-confidence is reflexively overconfident, so "95%, no
  evidence" is a real failure mode. The judge, by contrast, is independent *not
  because it's a different model* but because it grades **someone else's work** —
  a model scoring its own output would be self-grading again regardless of which
  model it is.
- **Confidence and groundedness are different signals from different owners.**
  `confidence` (how sure the author is) ≠ `groundedness` (are the claims actually
  supported by the context). A model can be confident *and* hallucinating; the
  independent verifier exists precisely to distrust the author's self-grade.
- **You can't skip a call by first making it (the gate circularity).** To *save*
  the judge call by branching on a trustworthy score, the score has to come from
  something you already have for free — which before the judge runs is only the
  author's self-report. Routing the gate signal through the judge means running
  the very call you wanted to skip. So: a cheap gate signal is necessarily a
  *weak* one; a strong signal necessarily costs the call. Pick the goal (save
  tokens **or** trust the branch), you can't have both at that decision point.
- **Calibrate self-report without extra calls.** Four zero-cost levers: (1) anchor
  the number to a **rubric** tied to how conclusive the evidence is; (2) require
  it be **justified by the evidence** the model already extracted; (3) **reason
  before scoring** — emit the number last, after root_cause/explanation/evidence,
  so the score follows the reasoning instead of leading it; (4) a **deterministic
  clamp** in code (cap confidence when the evidence list is thin) — prompts nudge,
  code enforces. Prompt-only calibration *reduces* but never *eliminates*
  overconfidence.
- **A self-feedback loop with no independent critic inflates confidence.** The
  judged refine loop works because it has two things — an independent critic *and*
  concrete per-dimension feedback. A "re-diagnose while confidence is low" loop
  on the un-judged path has neither: `failure_context` is frozen so there's no new
  evidence to find, and the loop's only exit is a higher number, so the model just
  bumps 40→90 and pads the evidence — actively undoing the calibration work. If
  you must retry, trigger on a *degenerate* output (empty evidence / missing
  fields), not on honest low confidence — an ambiguous failure *should* stay
  low-confidence.
- **Three axes of token optimization.** Fewer tokens *per call* (prune inputs —
  head+tail truncation of bodies/tracebacks keeps the signal, drops the middle;
  cap outputs; a strict JSON schema stops rambling). Fewer *calls* (bounded loops
  with early exit; gate escalation to the expensive model). Cheaper *tokens*
  (prefix-stable prompts so a caching layer can reuse the invariant system prompt;
  model tiering — cheap model for the common case, big model only when needed).
  Every input token cut is a recall-for-cost bet: you're trading a rarely-needed
  detail for a cheaper call.
- **Best-of-N is a deliberate *spend*, the mirror of everything else.** Sampling N
  diagnoses and picking by agreement (modal category) genuinely improves
  calibration because inter-sample agreement is a real signal — but at N× the
  calls. It's the honest way to buy accuracy on the un-judged path, and it belongs
  in the *cost* conversation, not the savings one.

## LLM application lifecycle

- **Two lifecycles; this project is inference-only.** The *model* lifecycle (data
  → pretrain → fine-tune → align → release → deprecate) happens **upstream** at the
  provider — Meta/OpenAI make the open weights, Groq serves them. This repo lives
  entirely in the *application* (LLMOps) lifecycle: the loop you run to build,
  ship, and improve a **feature** on an already-trained model. Tell: there is no
  training/fine-tuning code, so the only improvement levers are prompt, context,
  and orchestration — never weights.
- **The application loop, in order:** task framing → model selection → context/input
  engineering → prompt development → orchestration → guardrails → **offline eval** →
  deploy/serve → **online eval** → feedback/iterate → (back to prompt). The failure
  analyzer walks all of it; recognizing which stage a change touches keeps edits
  scoped.
- **Offline and online eval are different stages, not one.** Offline (`judge_case`
  over a golden dataset, gates CI) scores against a **reference answer** and can
  judge *correctness*. Online (`judge_live` on real failures) has **no reference**,
  so it drops correctness and scores only groundedness/completeness/actionability.
  Same judge, different applicability — the presence/absence of a ground-truth
  label is what splits the two.
- **A mature feedback loop runs at two timescales.** Fast + automated: the agentic
  refine loop (an independent critic's failed-dimension issues feed straight back
  into a re-diagnosis). Slow + human: offline eval surfaces a weakness → someone
  edits the prompt → PR. Stage 10 ("iterate") is the one most projects *talk* about
  and don't build; having *either* automated loop is the differentiator.
- **The MLOps maturity layer is the usual gap.** A working build→eval→serve→monitor
  loop still commonly lacks: prompt/model **versioning** as first-class artifacts,
  **drift/trend** tracking (per-run scores rolled up over time, not just this run's
  JSON), **cost/token telemetry**, and a **data flywheel** (production failures fed
  back to grow the golden set). These are what separate "it works" from "it's
  operable."
- **Token telemetry is free data you were throwing away.** Every Groq response already
  carries a `usage` block (prompt/completion/total tokens) on the wire — capturing
  it costs zero extra API calls; it was simply being discarded. `telemetry.py` now
  salvages it at both call sites and `conftest` appends one run-level row to
  `ai_analysis/token_usage.jsonl`. The design lesson: the useful signal isn't cost
  *alone* — it's cost **vs. quality** per run (does the refine loop's extra spend
  actually buy higher judge pass rates?), so the row co-locates tokens/cost with the
  judge pass-rate and mean confidence. Tokens are the durable, provider-independent
  metric; the dollar figure is a derived estimate from a dated price table. Two things
  it deliberately doesn't solve yet: cross-run persistence on ephemeral CI runners,
  and the fact that a "gate signal computed from the same call you're trying to skip"
  is circular — trend data informs the *next* run's config, it can't pre-empt the
  current call.