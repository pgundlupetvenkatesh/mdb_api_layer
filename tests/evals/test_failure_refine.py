"""
Unit tests for the agentic refine loop in :mod:`tests.helpers.failure_analyzer`.

Covers :func:`~tests.helpers.failure_analyzer.refine_until_confident`,
:func:`~tests.helpers.failure_analyzer._collect_issues`, and
:meth:`~tests.helpers.failure_analyzer.FailureAnalyzer.refine`. These are
offline, deterministic tests — the analyzer's ``_request_refined_diagnosis`` (the
refine path's Groq call) is monkeypatched and the judge is injected as a fake
callable, so no ``GROQ_API_KEY`` and no network are required.
"""

import allure
import pytest

from tests.helpers.failure_analyzer import (
    FailureAnalyzer,
    _collect_issues,
    refine_until_confident,
)

# Applies the unit marker to every test in the file at once, instead of decorating each class/test.
pytestmark = pytest.mark.unit
"""Mark every test in this module as an offline unit test (not a TMDB API test)."""


def _diagnosis(confidence, root_cause="stale movie id", test_name="test_a"):
    """Build a minimal diagnosis dict as the analyzer would return it."""
    return {
        "root_cause": root_cause,
        "category": "data_issue",
        "suggested_fix": "refresh the fixture id",
        "confidence": confidence,
        "explanation": "",
        "evidence": [],
        "test_name": test_name,
        "model": "llama",
    }


def _judgement(overall, groundedness="pass", completeness="pass", actionability="pass", issues=None):
    """Build a ``judge_live``-shaped verdict dict."""
    def dim(verdict):
        return {"verdict": verdict, "reasoning": "", "issues": issues or []}
    return {
        "groundedness": dim(groundedness),
        "completeness": dim(completeness),
        "actionability": dim(actionability),
        "overall_verdict": overall,
    }


def _sequenced_judge(verdicts):
    """A judge_fn that returns each verdict in turn (repeating the last), counting calls."""
    state = {"n": 0}

    def judge_fn(_ctx, _diag):
        verdict = verdicts[min(state["n"], len(verdicts) - 1)]
        state["n"] += 1
        return verdict

    return judge_fn, state


@pytest.fixture
def analyzer():
    """A force-enabled analyzer whose Groq call is stubbed per test."""
    instance = FailureAnalyzer()
    instance.enabled = True  # bypass env gating; _request_refined_diagnosis is monkeypatched per test
    return instance


@allure.epic("AI Evaluation")
@allure.feature("Agentic refine loop")
class TestRefineUntilConfident:
    """Behavior of :func:`refine_until_confident`."""

    @allure.story("Weak diagnosis is refined until judge-pass + confident")
    def test_refines_low_confidence_failing_diagnosis(self, analyzer):
        """A failing judge + low confidence triggers a refine that returns the improved diagnosis."""
        initial = _diagnosis(confidence=40)
        analyzer._results = [initial]
        improved = _diagnosis(confidence=95, root_cause="fixture id 550 was deleted")
        analyzer._request_refined_diagnosis = lambda *_a, **_k: improved
        judge_fn, _ = _sequenced_judge([_judgement("fail", groundedness="fail"), _judgement("pass")])

        final, judgement = refine_until_confident(
            analyzer, {"test_name": "test_a"}, initial, judge_fn,
            max_iterations=2, confidence_target=90,
        )

        assert final is improved
        assert final["confidence"] == 95
        assert judgement["overall_verdict"] == "pass"
        # The refined diagnosis replaces the stored one for that test.
        assert analyzer._results[-1] is improved

    @allure.story("Refine when judge passes but confidence misses the bar")
    def test_refines_when_only_confidence_below_target(self, analyzer):
        """Judge-pass at confidence 80 still refines up to the confidence target."""
        initial = _diagnosis(confidence=80)
        analyzer._results = [initial]
        improved = _diagnosis(confidence=92)
        calls = {"n": 0}

        def complete(*_a, **_k):
            calls["n"] += 1
            return improved

        analyzer._request_refined_diagnosis = complete
        judge_fn, _ = _sequenced_judge([_judgement("pass"), _judgement("pass")])

        final, _ = refine_until_confident(
            analyzer, {"test_name": "test_a"}, initial, judge_fn,
            max_iterations=2, confidence_target=90,
        )

        assert calls["n"] == 1  # one refine pass
        assert final["confidence"] == 92

    @allure.story("Loop is bounded by max_iterations")
    def test_stops_at_max_iterations(self, analyzer):
        """A persistently failing judge stops after max_iterations refine passes."""
        initial = _diagnosis(confidence=40)
        analyzer._results = [initial]
        calls = {"n": 0}

        def complete(*_a, **_k):
            calls["n"] += 1
            return _diagnosis(confidence=45)

        analyzer._request_refined_diagnosis = complete
        judge_fn, state = _sequenced_judge([_judgement("fail")])

        final, judgement = refine_until_confident(
            analyzer, {"test_name": "test_a"}, initial, judge_fn,
            max_iterations=2, confidence_target=90,
        )

        assert calls["n"] == 2  # exactly max_iterations refine passes
        assert state["n"] == 3  # initial judge + one re-judge per refine
        assert judgement["overall_verdict"] == "fail"

    @allure.story("A judge error stops the loop")
    def test_none_judgement_stops_immediately(self, analyzer):
        """When the judge returns None (API error), no refinement is attempted."""
        initial = _diagnosis(confidence=40)
        analyzer._results = [initial]
        calls = {"n": 0}
        analyzer._request_refined_diagnosis = lambda *_a, **_k: calls.__setitem__("n", calls["n"] + 1)
        judge_fn, _ = _sequenced_judge([None])

        final, judgement = refine_until_confident(
            analyzer, {"test_name": "test_a"}, initial, judge_fn,
            max_iterations=2, confidence_target=90,
        )

        assert calls["n"] == 0  # refine never called
        assert final is initial
        assert judgement is None


@allure.epic("AI Evaluation")
@allure.feature("Agentic refine loop")
class TestCollectIssues:
    """Behavior of :func:`_collect_issues`."""

    @allure.story("Only failed dimensions contribute issues")
    def test_collects_failed_dimension_issues(self):
        """Issues from failing dimensions are prefixed with the dimension name; passing ones are skipped."""
        judgement = _judgement("fail", groundedness="fail", issues=["invented a 404 status"])
        issues = _collect_issues(judgement)
        assert issues == ["groundedness: invented a 404 status"]

    @allure.story("A clean pass yields no issues")
    def test_empty_when_all_pass(self):
        """An all-pass judgement contributes no issues."""
        assert _collect_issues(_judgement("pass")) == []


@allure.epic("AI Evaluation")
@allure.feature("Agentic refine loop")
class TestRefine:
    """Behavior of :meth:`FailureAnalyzer.refine`."""

    @allure.story("Disabled analyzer refines to None")
    def test_returns_none_when_disabled(self, analyzer):
        """A disabled analyzer performs no completion and returns None."""
        analyzer.enabled = False
        called = {"n": 0}
        analyzer._request_refined_diagnosis = lambda *_a, **_k: called.__setitem__("n", called["n"] + 1)
        assert analyzer.refine({"test_name": "t"}, _diagnosis(40), []) is None
        assert called["n"] == 0

    @allure.story("Refinement appends when no prior result matches")
    def test_appends_when_no_matching_result(self, analyzer):
        """With an empty results list, the refined diagnosis is appended rather than replacing."""
        improved = _diagnosis(confidence=95)
        analyzer._request_refined_diagnosis = lambda *_a, **_k: improved
        result = analyzer.refine({"test_name": "test_a"}, _diagnosis(40), [])
        assert result is improved
        assert analyzer._results == [improved]