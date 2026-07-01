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
#   "meta-llama/llama-4-scout-17b-16e-instruct"
#   "qwen/qwen3-32b"
DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
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
        :returns: Parsed JSON diagnosis dict (keys: ``root_cause``, ``category``,
            ``suggested_fix``, ``confidence`` (0–100 int), ``explanation``, ``evidence``,
            ``test_name``, ``model``) or None if analysis is disabled/fails.
        """
        if not self.enabled:
            return None
        else:
            logger.info(f"AI_ANALYSIS_ENABLED={self.enabled} and GROQ_API_KEY {'set' if self.api_key else 'missing'}")

        prompt = self._build_prompt(failure_context)

        from groq.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
        messages = [
            ChatCompletionSystemMessageParam(role="system", content=SYSTEM_PROMPT),
            ChatCompletionUserMessageParam(role="user", content=prompt)
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
            diagnosis["test_name"] = failure_context.get("test_name", "unknown")
            diagnosis["model"] = self.model
            self._results.append(diagnosis)

            logger.info(f"🤖 AI Analysis [{diagnosis.get('category', '?')}]: {diagnosis.get('root_cause', 'N/A')}")
            return diagnosis

        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
            return None

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

# Singleton instance — shared across all tests in a session
analyzer = FailureAnalyzer()