"""
LLM-as-a-judge for the AI failure analyzer.

Sends a JSON payload (the failure context, the diagnosis under test, and —
for offline evaluation — the expected reference) to a judge model on Groq and
gets back a strict per-dimension verdict on whether the diagnosis is correct,
grounded, complete, and actionable.

Two modes share one judge call:

- :func:`judge_case` (offline eval) — scores all four dimensions. Correctness
  is scored against the case's ``expected`` reference; groundedness,
  completeness, and actionability are judged from ``failure_context`` alone.
- :func:`judge_live` (in-pytest, on real failures) — scores groundedness,
  completeness, and actionability (every dimension except correctness), because
  a real failure has no reference answer to score correctness against.

The judge runs on Groq (same provider as the analyzer it evaluates) but a
different model family — GPT-OSS judging Llama — so there is no self-preference
bias.

.. module:: evals.judge
   :synopsis: GPT-OSS-as-a-judge wrapper over Groq.
   :no-index:
"""

import json

from loguru import logger

from telemetry import ledger

DEFAULT_JUDGE_MODEL = "openai/gpt-oss-120b"

JUDGE_SYSTEM_PROMPT = """\
You are a strict, impartial evaluator of AI-generated API test failure diagnoses. You will receive a JSON object with three parts:

- "failure_context": the raw test failure information (test name, file, API URL, status code, response body, error message, traceback) that was given to a diagnosis model. This is the ONLY source of truth about what happened.
- "diagnosis": the diagnosis produced by that model, with fields: root_cause, category, suggested_fix, confidence, explanation, evidence.
- "expected": the reference answer, with expected_category (one of: api_bug | test_bug | data_issue | timeout | auth_error | schema_mismatch | environment) and expected_root_cause (a short gist of the true root cause).

Evaluate the diagnosis on exactly four dimensions and give each a verdict of "pass" or "fail":

1. correctness — Does the diagnosis identify the right failure cause?
   - FAIL if diagnosis.category does not exactly equal expected.expected_category.
   - FAIL if diagnosis.root_cause is not semantically consistent with expected.expected_root_cause (it need not match the wording, but it must describe the same underlying cause).
   - FAIL if diagnosis.suggested_fix addresses a different problem than expected.expected_root_cause describes.
   - Otherwise PASS.

2. groundedness — Is every claim supported by failure_context?
   - Check every factual claim in diagnosis.root_cause, diagnosis.explanation, and every item in diagnosis.evidence.
   - FAIL if any claim asserts a status code, field name, value, timing, URL, error text, or other fact that does not appear in, and cannot be directly derived from, failure_context. Paraphrase is fine; invention is not.
   - FAIL if any evidence item does not correspond to something actually present in failure_context.
   - Do NOT use the expected reference for this dimension; a diagnosis can be wrong yet grounded, or correct yet hallucinated.
   - Otherwise PASS.

3. completeness — Does the diagnosis cover the decisive signals?
   - FAIL if it ignores a key signal present in failure_context (e.g. the HTTP status code, the central error message, a timing value, or the specific assertion that failed) that a competent analyst would cite.
   - FAIL if any required field (root_cause, category, suggested_fix, confidence, explanation, evidence) is missing, empty, or filled with boilerplate that adds no information. Treat confidence as populated if it is a number between 0 and 100, even if encoded as a string.
   - Otherwise PASS.

4. actionability — Is suggested_fix a concrete, specific next step a developer could act on directly?
   - FAIL if suggested_fix is missing or empty.
   - FAIL if it is generic boilerplate that would fit almost any failure (e.g. "investigate the issue", "check the API", "review the test and fix it").
   - FAIL if it only names a direction without a concrete action (e.g. "handle the timeout better" fails; "raise exp_max_elp_secs above the observed 17.7s in the update_list test data" passes).
   - Judge only specificity and executability — a fix can be actionable even if it targets the wrong problem; that is correctness's concern, not this dimension's.
   - Otherwise PASS.

For each dimension provide 1-3 sentences of reasoning and a list of specific issues found (exact hallucinated claims, the missed signal, the category mismatch, the vague fix, etc.). Use an empty list when there are no issues.

Set overall_verdict to "pass" only if all four dimensions pass, otherwise "fail".

Be strict and literal. Judge only what is written; do not give credit for what the diagnosis "probably meant". Respond only with the required JSON object.\
"""

LIVE_JUDGE_SYSTEM_PROMPT = """\
You are a strict, impartial evaluator of AI-generated API test failure diagnoses. You will receive a JSON object with two parts:

- "failure_context": the raw test failure information (test name, file, API URL, status code, response body, error message, traceback) that was given to a diagnosis model. This is the ONLY source of truth about what happened.
- "diagnosis": the diagnosis produced by that model, with fields: root_cause, category, suggested_fix, confidence, explanation, evidence.

There is no reference answer here, so do NOT judge whether the diagnosis is correct. Evaluate exactly these three dimensions and give each a verdict of "pass" or "fail":

1. groundedness — Is every claim supported by failure_context?
   - Check every factual claim in diagnosis.root_cause, diagnosis.explanation, and every item in diagnosis.evidence.
   - FAIL if any claim asserts a status code, field name, value, timing, URL, error text, or other fact that does not appear in, and cannot be directly derived from, failure_context. Paraphrase is fine; invention is not.
   - FAIL if any evidence item does not correspond to something actually present in failure_context.
   - Otherwise PASS.

2. completeness — Does the diagnosis cover the decisive signals?
   - FAIL if it ignores a key signal present in failure_context (e.g. the HTTP status code, the central error message, a timing value, or the specific assertion that failed) that a competent analyst would cite.
   - FAIL if any required field (root_cause, category, suggested_fix, confidence, explanation, evidence) is missing, empty, or filled with boilerplate that adds no information. Treat confidence as populated if it is a number between 0 and 100, even if encoded as a string.
   - Otherwise PASS.

3. actionability — Is suggested_fix a concrete, specific next step a developer could act on directly?
   - FAIL if suggested_fix is missing or empty.
   - FAIL if it is generic boilerplate that would fit almost any failure (e.g. "investigate the issue", "check the API", "review the test and fix it").
   - FAIL if it only names a direction without a concrete action (e.g. "handle the timeout better" fails; "increase the read timeout above 30s" passes).
   - Judge only whether the fix is concrete and specific, not whether it actually solves the underlying problem.
   - Otherwise PASS.

For each dimension provide 1-3 sentences of reasoning and a list of specific issues found (exact hallucinated claims, the missed signal, the vague fix, etc.). Use an empty list when there are no issues.

Set overall_verdict to "pass" only if all three dimensions pass, otherwise "fail".

Be strict and literal. Judge only what is written; do not give credit for what the diagnosis "probably meant". Respond only with the required JSON object.\
"""

_DIMENSION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["verdict", "reasoning", "issues"],
    "properties": {
        "verdict": {"type": "string", "enum": ["pass", "fail"]},
        "reasoning": {"type": "string"},
        "issues": {"type": "array", "items": {"type": "string"}},
    },
}


def _output_schema(dimensions: tuple[str, ...]) -> dict:
    """
    Build the strict judge output schema for a given set of dimensions.

    :param dimensions: The dimension names the judge must return (e.g.
        ``("correctness", "groundedness", "completeness")``).
    :returns: A JSON Schema requiring one ``_DIMENSION_SCHEMA`` block per
        dimension plus an ``overall_verdict`` string. Example return::

            {
                "type": "object",
                "additionalProperties": False,
                "required": ["groundedness", "overall_verdict"],
                "properties": {
                    "groundedness": {  # one _DIMENSION_SCHEMA block per dimension
                        "type": "object",
                        "required": ["verdict", "reasoning", "issues"],
                        "properties": {...},
                    },
                    "overall_verdict": {"type": "string", "enum": ["pass", "fail"]},
                },
            }
    """
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [*dimensions, "overall_verdict"],
        "properties": {
            **{dim: _DIMENSION_SCHEMA for dim in dimensions},
            "overall_verdict": {"type": "string", "enum": ["pass", "fail"]},
        },
    }


JUDGE_OUTPUT_SCHEMA = _output_schema(("correctness", "groundedness", "completeness", "actionability"))
LIVE_JUDGE_OUTPUT_SCHEMA = _output_schema(("groundedness", "completeness", "actionability"))


def sanitize_diagnosis(diagnosis: dict) -> dict:
    """
    Clean an analyzer diagnosis before it is shown to the judge.

    The analyzer (``FailureAnalyzer.analyze``) injects two bookkeeping keys into
    its output — ``test_name`` and ``model``. We drop them so the judge sees
    only the model's actual answer and is never biased by knowing which model
    produced it. We also coerce ``confidence`` from a numeric string (the
    analyzer sometimes returns ``"90"``) to an int for a consistent type; a
    value we can't parse is left untouched because the judge prompt explicitly
    tolerates a non-int confidence.

    :param diagnosis: The raw diagnosis dict from the analyzer.
    :returns: A new dict safe to embed in a judge payload and a report
        (``test_name``/``model`` dropped, ``confidence`` coerced to int).
        Example return::

            {
                "root_cause": "Stale movie id 550 returned HTTP 404",
                "category": "data_issue",
                "suggested_fix": "Refresh the movie id used in test_data.yaml",
                "confidence": 90,
                "explanation": "The request to /movie/550 returned 404 Not Found...",
                "evidence": ["status_code 404", "error message 'could not be found'"],
            }
    """
    # rebuilds the diagnosis keeping every key except test_name and model so the judge can't be biased by knowing which
    # model wrote the answer
    cleaned = {k: v for k, v in diagnosis.items() if k not in ("test_name", "model")}
    if "confidence" in cleaned:
        try:
            # Parsing to int() for consistency in report and judge payload
            cleaned["confidence"] = int(str(cleaned["confidence"]).strip())
        except (ValueError, TypeError):
            pass  # leave as-is; the judge tolerates a non-int confidence
    return cleaned # stripped-and-normalized copy, ready to embed in a judge payload


def _call_judge(system_prompt: str, output_schema: dict, payload: dict, model: str, api_key: str | None) -> dict | None:
    """
    Make one judge call and return the parsed, validated verdict.

    Sends ``system_prompt`` plus the JSON-serialized ``payload`` to the judge
    model on Groq with strict structured outputs. If the account/model rejects
    strict ``json_schema``, it retries once with the looser ``json_object`` mode
    the analyzer itself uses. Any API error, unparseable response, or output
    missing a required key returns ``None`` (the caller treats that as a judge
    error rather than crashing).

    :param system_prompt: The judge instructions (full or live variant).
    :param output_schema: The strict JSON Schema for the expected output.
    :param payload: The judge input object to serialize into the user message.
    :param model: Groq model id for the judge.
    :param api_key: Groq API key; falls back to the client's env-based default.
    :returns: The parsed judge output, or ``None`` on failure.
        Example return::

            {
                "groundedness": {"verdict": "pass", "reasoning": "...", "issues": []},
                "completeness": {"verdict": "fail", "reasoning": "...",
                                 "issues": ["omits the 404 status code"]},
                "actionability": {"verdict": "pass", "reasoning": "...", "issues": []},
                "overall_verdict": "fail",
            }
    """
    # Lazy import
    from groq import Groq

    client = Groq(api_key=api_key)
    logger.debug(f"Sending user payload {json.dumps(payload, indent=2)}")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, indent=2)},
    ]
    # temperature — near-deterministic; a grader should be stable, not creative.
    # reasoning_effort — GPT model is a reasoning model; low effort keeps it cheap/fast as judging is a constrained task.
    # max_completion_tokens — headroom for the reasoning tokens GPT emits before the JSON.
    kwargs = dict(model=model, messages=messages, temperature=0.1, reasoning_effort="low", max_completion_tokens=1500)

    try:
        response = client.chat.completions.create(
            **kwargs,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "diagnosis_judgement", "strict": True, "schema": output_schema},
            },
        )
    except Exception as e:
        # Some models/accounts don't accept strict json_schema; retry with the
        # looser json_object mode the analyzer itself uses.
        logger.warning(f"Judge json_schema call failed ({e}); retrying with json_object")
        try:
            response = client.chat.completions.create(**kwargs, response_format={"type": "json_object"})
        except Exception as e2:
            logger.warning(f"Judge call failed: {e2}")
            return None

    # Salvage the free usage block (both create branches converge here) before
    # parsing — the judge tokens were spent regardless of the parse outcome.
    ledger.record(
        model=model,
        role="judge",
        usage=response.usage,
        test_name=payload.get("failure_context", {}).get("test_name", payload.get("case_id", "unknown")),
    )

    try:
        result = json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Judge returned unparseable JSON: {e}")
        return None

    # checks every key is present; if any is missing, log the keys for debugging and return none
    if not all(k in result for k in output_schema["required"]):
        logger.warning(f"Judge output missing required keys: {sorted(result)}")
        return None

    return result


def judge_case(payload: dict, model: str = DEFAULT_JUDGE_MODEL, api_key: str | None = None) -> dict | None:
    """
    Score one diagnosis on all four dimensions against its expected reference.

    Used by the offline eval, where each case carries an ``expected`` block.

    :param payload: The judge input object (``case_id``, ``failure_context``,
        ``diagnosis``, ``expected``).
    :param model: Groq model id for the judge. Defaults to DEFAULT_JUDGE_MODEL.
    :param api_key: Groq API key; falls back to the client's env-based default.
    :returns: The parsed judge output (per-dimension ``{verdict, reasoning,
        issues}`` for correctness/groundedness/completeness/actionability plus
        ``overall_verdict``), or ``None`` if the call or parse fails.
        Example return::

            {
                "correctness": {"verdict": "pass", "reasoning": "...", "issues": []},
                "groundedness": {"verdict": "pass", "reasoning": "...", "issues": []},
                "completeness": {"verdict": "pass", "reasoning": "...", "issues": []},
                "actionability": {"verdict": "pass", "reasoning": "...", "issues": []},
                "overall_verdict": "pass",
            }
    """
    return _call_judge(JUDGE_SYSTEM_PROMPT, JUDGE_OUTPUT_SCHEMA, payload, model, api_key)


def judge_live(failure_context: dict, diagnosis: dict, model: str = DEFAULT_JUDGE_MODEL, api_key: str | None = None) -> dict | None:
    """
    Score a live failure's diagnosis on groundedness, completeness, and actionability.

    Used in-pytest on live failures, which have no reference answer — so
    correctness is deliberately not judged. The diagnosis is cleaned with
    :func:`sanitize_diagnosis` before being shown to the judge.

    :param failure_context: The context the analyzer was given for this failure.
    :param diagnosis: The raw diagnosis the analyzer produced.
    :param model: Groq model id for the judge. Defaults to DEFAULT_JUDGE_MODEL.
    :param api_key: Groq API key; falls back to the client's env-based default.
    :returns: The parsed judge output (``groundedness``, ``completeness``,
        ``actionability``, ``overall_verdict``), or ``None`` if the call or
        parse fails. Example return::

            {
                "groundedness": {"verdict": "pass", "reasoning": "...", "issues": []},
                "completeness": {"verdict": "pass", "reasoning": "...", "issues": []},
                "actionability": {"verdict": "fail", "reasoning": "...",
                                  "issues": ["suggested_fix is too vague"]},
                "overall_verdict": "fail",
            }
    """
    payload = {"failure_context": failure_context, "diagnosis": sanitize_diagnosis(diagnosis)}
    return _call_judge(LIVE_JUDGE_SYSTEM_PROMPT, LIVE_JUDGE_OUTPUT_SCHEMA, payload, model, api_key)