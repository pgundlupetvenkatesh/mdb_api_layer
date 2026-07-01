"""
Unit tests for the pure helpers in :mod:`evals.judge`.

Covers :func:`~evals.judge.sanitize_diagnosis` and
:func:`~evals.judge._output_schema` (plus the two built schema constants).
These are offline, deterministic tests — no Groq call is made, so no
``GROQ_API_KEY`` is required (``_call_judge`` imports ``groq`` lazily).
"""

import allure
import pytest

from evals.judge import (
    JUDGE_OUTPUT_SCHEMA,
    LIVE_JUDGE_OUTPUT_SCHEMA,
    _output_schema,
    sanitize_diagnosis,
)

pytestmark = pytest.mark.unit
"""Mark every test in this module as an offline unit test (not a TMDB API test)."""


@allure.epic("AI Evaluation")
@allure.feature("Judge helpers")
class TestSanitizeDiagnosis:
    """Behavior of :func:`evals.judge.sanitize_diagnosis`."""

    @allure.story("Strip bookkeeping keys")
    def test_drops_test_name_and_model(self):
        """``test_name`` and ``model`` are removed; other keys are preserved."""
        cleaned = sanitize_diagnosis(
            {"category": "timeout", "test_name": "test_x", "model": "llama"}
        )
        assert "test_name" not in cleaned
        assert "model" not in cleaned
        assert cleaned["category"] == "timeout"

    @allure.story("Normalize confidence")
    def test_coerces_string_confidence_to_int(self):
        """A numeric-string ``confidence`` is coerced to ``int``."""
        assert sanitize_diagnosis({"confidence": "90"})["confidence"] == 90

    @allure.story("Normalize confidence")
    def test_leaves_unparseable_confidence(self):
        """A non-numeric ``confidence`` is left untouched (the judge tolerates it)."""
        assert sanitize_diagnosis({"confidence": "high"})["confidence"] == "high"

    @allure.story("Purity")
    def test_does_not_mutate_input(self):
        """The original diagnosis dict is not modified; a new dict is returned."""
        original = {"category": "timeout", "model": "llama"}
        sanitize_diagnosis(original)
        assert original == {"category": "timeout", "model": "llama"}


@allure.epic("AI Evaluation")
@allure.feature("Judge helpers")
class TestOutputSchema:
    """Shape of the strict judge output schema from :func:`evals.judge._output_schema`."""

    @allure.story("Schema shape")
    def test_requires_each_dimension_plus_overall(self):
        """``required`` lists every dimension plus ``overall_verdict`` in order."""
        schema = _output_schema(("groundedness", "completeness"))
        assert schema["required"] == ["groundedness", "completeness", "overall_verdict"]
        assert set(schema["properties"]) == {"groundedness", "completeness", "overall_verdict"}
        assert schema["additionalProperties"] is False

    @allure.story("Schema shape")
    def test_offline_schema_has_four_dimensions(self):
        """The offline schema scores all four dimensions."""
        dims = set(JUDGE_OUTPUT_SCHEMA["properties"]) - {"overall_verdict"}
        assert dims == {"correctness", "groundedness", "completeness", "actionability"}

    @allure.story("Schema shape")
    def test_live_schema_excludes_correctness(self):
        """The live schema drops correctness (no reference answer live)."""
        dims = set(LIVE_JUDGE_OUTPUT_SCHEMA["properties"]) - {"overall_verdict"}
        assert dims == {"groundedness", "completeness", "actionability"}