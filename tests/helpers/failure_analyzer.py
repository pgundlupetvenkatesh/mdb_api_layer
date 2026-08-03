"""
AI-powered test failure analyzer using open-source LLMs via Groq.

Sends test failure context (error, test code, API response) to an LLM
and returns a structured diagnosis with root cause, suggested fix, and
failure classification.

.. module:: tests.helpers.failure_analyzer
   :synopsis: LLM-based test failure analysis.
   :no-index:
"""

import os
import json
from pathlib import Path
from loguru import logger

# Model options on Groq free tier:
#   "llama-3.3-70b-versatile"
#   "qwen/qwen3-32b"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = """
You are an expert API test failure analyst. When given a test failure context, analyze it and respond with a JSON object containing:
{
  "root_cause": "One sentence explaining why the test failed",
  "category": "one of: api_bug | test_bug | data_issue | timeout | auth_error | schema_mismatch | environment",
  "suggested_fix": "Specific actionable fix in 1-2 sentences",
  "confidence": "integer between 0 and 100 representing how confident you are in the diagnosis (e.g. 90 means 90% confident)",
  "explanation": "2-3 sentence detailed explanation of what went wrong",
  "evidence": ["list of observable facts from logs/errors that support the diagnosis, e.g. HTTP status code, response body snippets, error messages"]
}

Rules:
- api_bug: The API returned an unexpected response (status code, missing field, wrong value)
- test_bug: The test assertion or logic is incorrect
- data_issue: Test data is stale, invalid, or the resource was deleted
- timeout: Response time exceeded the threshold
- auth_error: Authentication/authorization failure (expired token, missing key)
- schema_mismatch: Response structure doesn't match the expected Pydantic model or contract
- environment: Configuration, connectivity, or environment setup issue
- Be concise and specific to the TMDB API domain
- Respond ONLY with valid JSON, no markdown fences
"""

# Used by the agentic refine loop: the same output contract as SYSTEM_PROMPT,
# plus an instruction to address an independent reviewer's critique of a prior
# diagnosis. Confidence must reflect genuine evidential support, not the target.
REFINE_SYSTEM_PROMPT = SYSTEM_PROMPT + """
You are refining a previous diagnosis that an independent reviewer judged weak. Address the
reviewer's specific issues, ground every claim in the provided evidence, and make the
suggested_fix concrete. Return the same JSON object. Only raise confidence if the improved
diagnosis is genuinely better supported by the evidence — never inflate it to hit a target.
"""

class FailureAnalyzer:
    """
    Analyzes test failures using an open-source LLM via Groq's free API.

    Disabled by default. Enable by setting AI_ANALYSIS_ENABLED=true and
    GROQ_API_KEY in the .env file.

    :param model: The LLM model identifier to use on Groq.
    """

    def __init__(self, model: str = None):
        """
        Initialize the failure analyzer.

        Reads configuration from environment variables at construction time.
        If ``AI_ANALYSIS_ENABLED`` is ``true`` but ``GROQ_API_KEY`` is missing,
        analysis is automatically disabled with a warning.

        :param model: LLM model identifier to use on Groq. Falls back to
            the ``AI_MODEL`` env var, then ``DEFAULT_MODEL``.
        """
        self.enabled = os.getenv("AI_ANALYSIS_ENABLED", "false").lower() == "true"
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("AI_MODEL", DEFAULT_MODEL)
        self._client = None
        self._results = []

        if self.enabled and not self.api_key:
            logger.warning("AI_ANALYSIS_ENABLED=true but GROQ_API_KEY is not set. Disabling AI analysis.")
            self.enabled = False

    @property
    def client(self):
        """
        Lazy-initialize the Groq client on first access.

        Delays the ``from groq import Groq`` import until analysis is
        actually needed, avoiding import errors when the ``groq`` package
        is installed but never used.

        :returns: Configured ``groq.Groq`` client instance.
        """
        if self._client is None:

            from groq import Groq
            self._client = Groq(api_key=self.api_key)

        return self._client

    @property
    def results(self) -> list[dict]:
        """All diagnoses accumulated this session (read-only view)."""
        return self._results

    def analyze(self, failure_context: dict) -> dict | None:
        """
        Send failure context to the LLM and return structured diagnosis.

        :param failure_context: Dictionary containing failure details:
            - test_name: Name of the failed test
            - test_file: Path to the test file
            - error_message: The assertion or exception message
            - traceback: Full traceback string
            - api_url: The API URL that was called (if available)
            - status_code: HTTP status code received (if available)
            - response_body: API response body snippet (if available)
        :returns: Parsed JSON diagnosis dict, or None if analysis is
            disabled/fails. Example return::

                {
                    "root_cause": "Movie id 0 is invalid, so TMDB returned 404.",
                    "category": "data_issue",
                    "suggested_fix": "Use a valid movie id from movie_ids.txt in the test data.",
                    "confidence": 92,
                    "explanation": "The request targeted /3/movie/0; TMDB rejects id 0 ...",
                    "evidence": ["HTTP 404", "status_message: The resource you requested could not be found."],
                    "test_name": "test_get_movie_details",
                    "model": "llama-3.3-70b-versatile"
                }
        """
        if not self.enabled:
            return None
        else:
            logger.info(f"AI_ANALYSIS_ENABLED={self.enabled} and GROQ_API_KEY {'set' if self.api_key else 'missing'}")

        prompt = self._build_prompt(failure_context)
        diagnosis = self._request_diagnosis(SYSTEM_PROMPT, prompt, failure_context.get("test_name", "unknown"))
        if diagnosis is None:
            return None

        self._results.append(diagnosis)
        logger.info(f"🤖 AI Analysis [{diagnosis.get('category', '?')}]: {diagnosis.get('root_cause', 'N/A')}")
        return diagnosis

    def _request_diagnosis(self, system_prompt: str, user_prompt: str, test_name: str) -> dict | None:
        """
        Run one LLM completion and return a parsed, normalized diagnosis dict.

        Shared by :meth:`analyze` (initial diagnosis) and :meth:`refine`
        (judge-guided improvement). Handles the Groq call, JSON parse,
        ``test_name``/``model`` stamping, and ``confidence`` int-coercion.
        Does **not** touch ``self._results`` — the caller decides whether to
        append (a new diagnosis) or replace (a refinement).

        :param system_prompt: System message controlling the JSON output contract.
        :param user_prompt: The assembled failure (or critique) prompt.
        :param test_name: Name of the failed test, stamped onto the result.
        :returns: Normalized diagnosis dict (same shape as :meth:`analyze`'s
            return), or None if the call/parse fails.
        """
        from groq.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
        messages = [
            ChatCompletionSystemMessageParam(role="system", content=system_prompt),
            ChatCompletionUserMessageParam(role="user", content=user_prompt)
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,        # Low temperature for consistent analysis
                max_tokens=500,
                response_format={"type": "json_object"}  # noqa: type stubs missing in groq v1.x
            )

            raw = response.choices[0].message.content
            diagnosis = json.loads(raw)
            diagnosis["test_name"] = test_name
            diagnosis["model"] = self.model
            # llama-3.3-70b sometimes returns confidence as a string ("95");
            # downstream tiering compares it numerically, so coerce here.
            try:
                diagnosis["confidence"] = int(diagnosis.get("confidence", 0))
            except (TypeError, ValueError):
                diagnosis["confidence"] = 0
            return diagnosis

        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
            return None

    # Alias used by refine() — same completion call, named for the refinement context.
    _request_refined_diagnosis = _request_diagnosis

    def refine(self, failure_context: dict, prior_diag: dict, weaknesses: list[str]) -> dict | None:
        """
        Produce an improved diagnosis given a critique of a prior one.

        Called by :func:`refine_until_confident` when the independent judge
        flags a diagnosis. Re-prompts the model with the original failure
        context, the prior diagnosis, and the judge's concrete ``weaknesses``,
        asking it to address each one and re-examine the evidence. The improved
        diagnosis **replaces** the prior one in ``self._results`` (matched by
        ``test_name``) so the saved report and terminal summary reflect the
        final version.

        :param failure_context: Same dict passed to :meth:`analyze`.
        :param prior_diag: The diagnosis being critiqued.
        :param weaknesses: Concrete weaknesses from the judge to address.
        :returns: Improved diagnosis dict (same shape as :meth:`analyze`'s
            return), or None if analysis is disabled or the call fails.
        """
        if not self.enabled:
            return None

        prompt = self._build_refine_prompt(failure_context, prior_diag, weaknesses)
        diagnosis = self._request_refined_diagnosis(REFINE_SYSTEM_PROMPT, prompt, failure_context.get("test_name", "unknown"))
        if diagnosis is None:
            return None

        if self._results and self._results[-1].get("test_name") == diagnosis["test_name"]:
            self._results[-1] = diagnosis
        else:
            self._results.append(diagnosis)

        logger.info(
            f"🤖 AI Refine [{diagnosis.get('category', '?')}] "
            f"confidence {diagnosis.get('confidence', '?')}%: {diagnosis.get('root_cause', 'N/A')}"
        )
        return diagnosis

    @staticmethod
    def _build_prompt(ctx: dict) -> str:
        """
        Build the user prompt string from failure context.

        Assembles a structured text prompt containing test name, file path,
        API URL, status code, response body (truncated to 2000 chars with
        head+tail strategy), error message, and the last 20 lines of the
        traceback. Only includes fields that are present in the context dict.

        :param ctx: Dictionary of failure details (same keys as ``analyze()``'s
            ``failure_context`` parameter).
        :returns: Formatted multi-line string ready to send to the LLM.
        """
        parts = [f"Test: {ctx.get('test_name', 'unknown')}"]

        if ctx.get("test_file"):
            parts.append(f"File: {ctx['test_file']}")
        if ctx.get("api_url"):
            parts.append(f"API URL: {ctx['api_url']}")
        if ctx.get("status_code"):
            parts.append(f"Status Code: {ctx['status_code']}")
        if ctx.get("response_body"):
            # Truncate large responses
            body = str(ctx["response_body"])
            if len(body) > 2000:
                # Capturing both start and end of the response body...
                body = body[:1000] + "\n...[truncated]...\n" + body[-500:]
            parts.append(f"Response Body: {body}")
        if ctx.get("error_message"):
            parts.append(f"Error: {ctx['error_message']}")
        if ctx.get("traceback"):
            # Last 20 lines of traceback
            tb_lines = ctx["traceback"].strip().split("\n")[-20:]
            parts.append(f"Traceback:\n{chr(10).join(tb_lines)}")

        return "\n".join(parts)

    @staticmethod
    def _build_refine_prompt(ctx: dict, prior_diag: dict, weaknesses: list[str]) -> str:
        """
        Build the critique prompt for a refinement pass.

        Combines the original failure context with the prior diagnosis and the
        judge's concrete weaknesses, instructing the model to address each one,
        re-examine the evidence, and emit an improved diagnosis in the same JSON
        contract. The bookkeeping keys (``test_name``/``model``) are dropped from
        the echoed prior so the model focuses on the diagnosis content.

        :param ctx: The original failure context (see :meth:`analyze`).
        :param prior_diag: The diagnosis being critiqued.
        :param weaknesses: Concrete weaknesses raised by the judge (may be empty
            when only the confidence bar was missed).
        :returns: Formatted multi-line prompt string.
        """
        weakness_lines = (
            "\n".join(f"- {weakness}" for weakness in weaknesses)
            if weaknesses
            else "- Confidence is below the required bar; strengthen the evidence and reasoning."
        )
        prior_json = json.dumps(
            {k: v for k, v in prior_diag.items() if k not in ("test_name", "model")}, indent=2
        )
        return (
            f"{FailureAnalyzer._build_prompt(ctx)}\n\n"
            f"An independent reviewer judged your previous diagnosis and found these weaknesses:\n"
            f"{weakness_lines}\n\n"
            f"Previous diagnosis:\n{prior_json}\n\n"
            "Address every weakness above, re-examine the evidence, and return an improved "
            "diagnosis in the same JSON format."
        )

    def save_results(self, output_dir: str = "ai_analysis"):
        """
        Write all accumulated analysis results to a JSON file.

        Called once at the end of the test session by ``pytest_sessionfinish``
        in ``conftest.py``. Skips writing if no failures were analyzed.
        Creates the output directory if it doesn't exist.

        :param output_dir: Directory path to write the results file to.
            Defaults to ``ai_analysis/`` relative to the project root.

        Output file: ``<output_dir>/failure_analysis.json``
        """
        if not self._results:
            return

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        report_file = out_path / "failure_analysis.json"
        report_file.write_text(json.dumps(self._results, indent=2))
        logger.info(f"📊 AI analysis report saved: {report_file} ({len(self._results)} failures analyzed)")

def _collect_issues(judgement: dict) -> list[str]:
    """
    Gather concrete issues from a judgement's failed dimensions.

    Pulls the ``issues`` list from each of groundedness/completeness/
    actionability whose verdict is ``fail``, prefixing each with its dimension
    so the refine prompt knows what to fix.

    :param judgement: A ``judge_live`` result dict.
    :returns: Flat list of ``"<dimension>: <issue>"`` strings (possibly empty), e.g.::

        [
            "groundedness: Speculative causes in explanation not found in failure_context",
            "completeness: Diagnosis omits the HTTP status code from the response",
        ]
    """
    collected = []
    for dim in ("groundedness", "completeness", "actionability"):
        section = judgement.get(dim)
        if isinstance(section, dict) and section.get("verdict") == "fail":
            collected.extend(f"{dim}: {issue}" for issue in section.get("issues", []))
    return collected


def refine_until_confident(
    analyzer_instance, failure_context, diagnosis, judge_fn, *, max_iterations, confidence_target
):
    """
    Iteratively improve a diagnosis using an independent judge as the critic.

    Agentic loop: judge the current diagnosis; if the judge passes **and** the
    self-reported ``confidence`` clears ``confidence_target``, stop. Otherwise
    feed the judge's failed-dimension issues back into
    :meth:`FailureAnalyzer.refine` and re-judge, up to ``max_iterations`` times.

    The judge is injected (``judge_fn``) so this module stays decoupled from
    ``evals.judge`` and the loop is unit-testable. A ``None`` judgement (judge
    API error) stops the loop — without a critic signal there is nothing to
    refine against.

    :param analyzer_instance: The :class:`FailureAnalyzer` that produced ``diagnosis``.
    :param failure_context: The failure context dict.
    :param diagnosis: The initial diagnosis from :meth:`FailureAnalyzer.analyze`.
    :param judge_fn: Callable ``(failure_context, diagnosis) -> judgement | None``.
    :param max_iterations: Maximum number of refine passes.
    :param confidence_target: Confidence (0–100) the diagnosis must reach.
    :returns: Tuple of the final ``(diagnosis, judgement)`` — the diagnosis has
        the shape shown in :meth:`FailureAnalyzer.analyze`, the judgement is the
        ``judge_fn`` output (or ``None`` if the judge errored). Example return::

            (
                {"root_cause": "...", "category": "data_issue", "confidence": 92, ...},
                {
                    "groundedness": {"verdict": "pass", "reasoning": "...", "issues": []},
                    "completeness": {"verdict": "pass", "reasoning": "...", "issues": []},
                    "actionability": {"verdict": "pass", "reasoning": "...", "issues": []},
                    "overall_verdict": "pass",
                },
            )
    """
    # In production, the real judge, in conftest.py (~line 405) gets passed. judge_fn is a thin lambda wrapping
    # evals.judge.judge_live — It pre-binds the model/api_key args.
    judgement = judge_fn(failure_context, diagnosis) # judge the current diagnosis

    for _ in range(max_iterations):
        if judgement is None:
            break
        passing = judgement.get("overall_verdict") == "pass"
        confident = diagnosis.get("confidence", 0) >= confidence_target
        if passing and confident:
            break

        refined = analyzer_instance.refine(failure_context, diagnosis, _collect_issues(judgement))
        if refined is None:
            break
        diagnosis = refined
        judgement = judge_fn(failure_context, diagnosis) # re-judge the refined diagnosis

    return diagnosis, judgement


# Singleton instance — shared across all tests in a session
analyzer = FailureAnalyzer()