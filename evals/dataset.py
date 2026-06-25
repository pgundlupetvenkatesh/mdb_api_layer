"""
Golden-dataset loader for the failure-analyzer evaluation.

Reads the curated YAML dataset of TMDB failure contexts (one or more per
diagnosis category) and validates each case has the structure the runner and
judge expect. The dataset is the ground truth the judge scores correctness
against, so a malformed case is a hard error rather than a silent skip.

.. module:: evals.dataset
   :synopsis: Load and validate the eval golden dataset.
"""

from pathlib import Path

import yaml

# Must stay in sync with the ``category`` enum in the analyzer's SYSTEM_PROMPT
# (tests/helpers/failure_analyzer.py).
VALID_CATEGORIES = {
    "api_bug",
    "test_bug",
    "data_issue",
    "timeout",
    "auth_error",
    "schema_mismatch",
    "environment",
}


def load_dataset(path: str | Path) -> list[dict]:
    """
    Load and validate the golden eval dataset.

    :param path: Path to the YAML dataset (a mapping with a top-level
        ``cases`` list).
    :returns: The list of case dicts, each with ``id``, ``failure_context``,
        and ``expected`` keys.
    :raises ValueError: If the file is malformed or any case is missing a
        required field, has a duplicate ``id``, or names a category outside
        :data:`VALID_CATEGORIES`. The message names the offending case.
    """
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
        raise ValueError(f"{path}: expected a mapping with a 'cases' list")

    cases = data["cases"]
    if not cases:
        raise ValueError(f"{path}: dataset has no cases")

    seen_ids: set[str] = set()
    for i, case in enumerate(cases):
        case_id = case.get("id")
        label = case_id or f"case[{i}]"
        if not case_id:
            raise ValueError(f"{label}: missing 'id'")
        if case_id in seen_ids:
            raise ValueError(f"{case_id}: duplicate 'id'")
        seen_ids.add(case_id)

        ctx = case.get("failure_context")
        if not isinstance(ctx, dict) or not ctx.get("test_name"):
            raise ValueError(f"{case_id}: failure_context.test_name is required")

        expected = case.get("expected")
        if not isinstance(expected, dict):
            raise ValueError(f"{case_id}: missing 'expected' block")
        category = expected.get("expected_category")
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"{case_id}: expected.expected_category {category!r} not in "
                f"{sorted(VALID_CATEGORIES)}"
            )
        if not expected.get("expected_root_cause"):
            raise ValueError(f"{case_id}: expected.expected_root_cause is required")

    return cases