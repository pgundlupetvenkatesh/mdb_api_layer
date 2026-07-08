"""
Unit tests for :func:`evals.dataset.load_dataset` validation. Covering deterministic logic.

Pure offline tests — no API, no Groq, no ``GROQ_API_KEY`` needed. Each case is
written to a temporary YAML file and fed to the loader to exercise its
fail-fast branches (the loader raises ``ValueError`` naming the offending case).
"""

import allure
import pytest
import yaml


from evals.dataset import load_dataset

pytestmark = pytest.mark.unit
"""Mark every test in this module as an offline unit test (not a TMDB API test)."""


def _valid_case() -> dict:
    """
    Build a minimal well-formed dataset case.

    :returns: A case dict with the ``id``, ``failure_context`` (with
        ``test_name``), and ``expected`` (category + root cause) the loader
        requires. Individual tests mutate a copy to trigger one error at a time.
    """
    return {
        "id": "timeout_case",
        "failure_context": {"test_name": "test_x", "status_code": 201},
        "expected": {
            "expected_category": "timeout",
            "expected_root_cause": "the call took longer than the threshold",
        },
    }


def _write(tmp_path, data: dict):
    """
    Serialize ``data`` to a YAML file under ``tmp_path``.

    :param tmp_path: Pytest ``tmp_path`` fixture (a unique temp directory).
    :param data: The dataset mapping to dump.
    :returns: Path to the written YAML file.
    """
    path = tmp_path / "dataset.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


@allure.epic("AI Evaluation")
@allure.feature("Golden dataset loader")
class TestLoadDataset:
    """Validation behavior of :func:`evals.dataset.load_dataset`."""

    @allure.story("Valid dataset")
    def test_loads_valid_dataset(self, tmp_path):
        """A well-formed dataset returns its list of cases unchanged.

        :param tmp_path: Pytest temp-dir fixture for the dataset file.
        """
        with allure.step("Load a single-case dataset"):
            cases = load_dataset(_write(tmp_path, {"cases": [_valid_case()]}))
        assert len(cases) == 1
        assert cases[0]["id"] == "timeout_case"

    @allure.story("Structural errors")
    @pytest.mark.parametrize(
        "payload, match",
        [
            ({}, "cases"),
            ({"cases": "notalist"}, "cases"),
            ({"cases": []}, "no cases"),
        ],
    )
    def test_rejects_bad_top_level(self, tmp_path, payload, match):
        """The top-level document must be a mapping with a non-empty ``cases`` list.

        :param tmp_path: Pytest temp-dir fixture.
        :param payload: A malformed top-level document.
        :param match: Substring expected in the raised ``ValueError``.
        """
        with pytest.raises(ValueError, match=match):
            load_dataset(_write(tmp_path, payload))

    @allure.story("Per-case errors")
    @pytest.mark.parametrize(
        "mutate, match",
        [
            (lambda c: c.pop("id"), "missing 'id'"),
            (lambda c: c["failure_context"].pop("test_name"), "test_name is required"),
            (lambda c: c.pop("failure_context"), "test_name is required"),
            (lambda c: c.pop("expected"), "missing 'expected'"),
            (lambda c: c["expected"].__setitem__("expected_category", "bogus"), "not in"),
            (lambda c: c["expected"].pop("expected_root_cause"), "expected_root_cause is required"),
        ],
    )
    def test_rejects_invalid_case(self, tmp_path, mutate, match):
        """Each required per-case field is enforced with a naming ``ValueError``.

        :param tmp_path: Pytest temp-dir fixture.
        :param mutate: A function that breaks one field of a valid case in place.
        :param match: Substring expected in the raised ``ValueError``.
        """
        case = _valid_case()
        mutate(case)
        with pytest.raises(ValueError, match=match):
            load_dataset(_write(tmp_path, {"cases": [case]}))

    @allure.story("Per-case errors")
    def test_rejects_duplicate_id(self, tmp_path):
        """Two cases sharing an ``id`` raise a duplicate-id error.

        :param tmp_path: Pytest temp-dir fixture.
        """
        with pytest.raises(ValueError, match="duplicate 'id'"):
            load_dataset(_write(tmp_path, {"cases": [_valid_case(), _valid_case()]}))