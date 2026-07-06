"""
CLI runner for the failure-analyzer evaluation.

Runs the AI failure analyzer (Llama 3.3 70B via Groq) live on each case in the
golden dataset, then judges every produced diagnosis with the GPT-OSS judge on
four dimensions (correctness, groundedness, completeness, actionability). Prints
a per-case table plus aggregate metrics and writes a JSON report.

Both the analyzer under test and the judge call Groq, so only ``GROQ_API_KEY``
is required.

Usage::

    poetry run python -m evals
    poetry run python -m evals --judge-model openai/gpt-oss-120b
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from evals.dataset import load_dataset
from evals.judge import DEFAULT_JUDGE_MODEL, judge_case, sanitize_diagnosis

DEFAULT_DATASET = "evals/golden_dataset.yaml"
DEFAULT_OUTPUT = "evals/results/eval_results.json"
DIMENSIONS = ("correctness", "groundedness", "completeness", "actionability")


def _make_scout():
    """
    Build a fresh, force-enabled analyzer instance.

    Mirrors how ``tests/conftest.py`` force-enables analysis under
    ``--failure-analysis`` (sets ``enabled`` and re-reads the key), but on a new
    instance rather than the module singleton — so the eval never appends to the
    singleton's ``_results`` or writes ``ai_analysis/``, and works regardless of
    the ``AI_ANALYSIS_ENABLED`` env var.

    :returns: A ready-to-use ``FailureAnalyzer``.
    """
    from tests.helpers.failure_analyzer import FailureAnalyzer

    scout = FailureAnalyzer() # Here self.enabled is whatever AI_ANALYSIS_ENABLED is; likely false during an eval run
    scout.enabled = True
    scout.api_key = os.getenv("GROQ_API_KEY")
    return scout


def _build_payload(case: dict, diagnosis: dict) -> dict:
    """
    Assemble the single JSON object sent to the judge for one case.

    The payload bundles the three things the judge needs: the ``failure_context``
    the analyzer saw, the ``diagnosis`` it produced (already cleaned), and the
    ``expected`` reference answer the dataset author wrote.

    The ``failure_context`` is fed to Scout to produce the *whole* diagnosis, and
    that one diagnosis is then judged on all four dimensions — ``failure_context``
    is not tied to any single dimension. What sets correctness apart is the judge,
    not the input: correctness compares Scout's ``diagnosis`` (its ``category`` and
    ``root_cause``) against ``expected`` — the known-true answer a human authored
    for this case — so it needs that reference to grade against. Groundedness,
    completeness, and actionability need no reference: they judge the diagnosis
    against the ``failure_context`` evidence itself, asking whether it is
    internally sound, not whether it is *right*.

    This is why correctness is an offline-only dimension. ``expected`` exists only
    in the curated dataset; it is hand-written by someone who already knew the true
    cause, and is *not* derivable from ``failure_context`` (if it were, we would not
    need Scout). A live failure has no such answer key — so ``judge_live`` drops
    correctness and scores only the other three. This is the exact shape
    ``judge.judge_case`` documents and ``JUDGE_SYSTEM_PROMPT`` describes.

    How it differs from the live path

      ┌──────────────────────┬───────────────────────────────────────────────┬─────────────────────────────┐
      │                      │           _build_payload (offline)            │ judge_live's inline payload │
      ├──────────────────────┼───────────────────────────────────────────────┼─────────────────────────────┤
      │ keys                 │ case_id, failure_context, diagnosis, expected │ failure_context, diagnosis  │
      ├──────────────────────┼───────────────────────────────────────────────┼─────────────────────────────┤
      │ expected?            │ yes (enables correctness)                     │ no (no reference)           │
      ├──────────────────────┼───────────────────────────────────────────────┼─────────────────────────────┤
      │ sanitizes diagnosis? │ no — caller already did                       │ yes — inline                │
      └──────────────────────┴───────────────────────────────────────────────┴─────────────────────────────┘

    :param case: A dataset case (``id``, ``failure_context``, ``expected``) from :func:`evals.dataset.load_dataset`
    :param diagnosis: The cleaned diagnosis for that case.
    :returns: The judge input object.
    """
    return {
        "case_id": case["id"],
        "failure_context": case["failure_context"],
        "diagnosis": diagnosis,
        "expected": case["expected"],
    }


def _diagnose_cases(cases: list[dict]) -> list[dict]:
    """
    Run the analyzer once per dataset case and collect the diagnoses.

    Uses a single fresh analyzer instance (see :func:`_make_scout`) for the
    whole pass. For each case it calls ``analyze(failure_context)`` and records
    the produced diagnosis. ``analyze`` returns ``None`` when the analyzer's own
    LLM call fails; that is captured as ``scout_failure`` so the case is carried
    through the report (and excluded from quality metrics) rather than crashing
    the run.

    Exercise the analyzer (Llama 3.3 70B) on known inputs. Each dataset case carries a
    realistic ``failure_context``; this function feeds that context to a fresh
    ``FailureAnalyzer`` and captures what the analyzer model says. This is the only
    place in the eval where the system-under-test actually runs.

    Purpose: Take the golden dataset and produce one diagnosis per case from
    the live analyzer — the raw material the judge will later grade.

    :param cases: The validated dataset cases.
    :returns: One record per case, each with ``case_id``, ``expected_category``
        (lifted out for the table/metrics), the cleaned ``diagnosis`` (or
        ``None``), and a ``scout_failure`` flag.
    """
    scout = _make_scout()
    records = []
    for case in cases:
        logger.info(f"Diagnosing {case['id']}")
        diagnosis = scout.analyze(case["failure_context"])
        records.append(
            {
                "case_id": case["id"],
                "expected_category": case["expected"]["expected_category"],
                "diagnosis": sanitize_diagnosis(diagnosis) if diagnosis else None,
                "scout_failure": diagnosis is None,
            }
        )
    return records


def _judge_records(records: list[dict], cases_by_id: dict, model: str, api_key: str) -> None:
    """
    Score every diagnosed record with the judge, mutating each record in place.

    For each record it: (1) skips analyzer failures, marking them as not passing;
    (2) computes ``category_match`` directly in code (exact string compare of the
    diagnosed category vs. the expected one) — this is deterministic and does not
    rely on the judge; (3) calls :func:`judge.judge_case` and stores the raw judge
    output under ``judge``; (4) recomputes ``overall_pass`` here as "all four
    dimensions passed" rather than trusting the judge's own ``overall_verdict``,
    so the headline pass/fail is always consistent with the per-dimension verdicts.
    A judge that errors or returns malformed JSON is recorded as ``judge_error``.

    :param records: Records from :func:`_diagnose_cases`.
    :param cases_by_id: The dataset keyed by case id, to rebuild each judge payload.
    :param model: Judge model id.
    :param api_key: Groq API key for the judge.
    """
    for record in records:
        if record["scout_failure"]:
            record.update(category_match=False, judge=None, judge_error=False, overall_pass=False)
            continue

        case = cases_by_id[record["case_id"]]
        record["category_match"] = (
            record["diagnosis"].get("category") == record["expected_category"]
        )

        logger.info(f"Judging {record['case_id']}")
        judgement = judge_case(_build_payload(case, record["diagnosis"]), model=model, api_key=api_key)
        if judgement is None:
            record.update(judge=None, judge_error=True, overall_pass=False)
            continue

        # Recompute overall in code — never trust the judge's own overall_verdict for aggregates.
        record["judge"] = judgement
        record["judge_error"] = False
        record["overall_pass"] = all(
            judgement[dim]["verdict"] == "pass" for dim in DIMENSIONS
        )


def _summarize(records: list[dict]) -> dict:
    """
    Roll the per-case records up into the report's aggregate ``summary`` block.

    Every number here is just a count or a count/total fraction:

    - ``scout_failures`` / ``judge_errors`` — how many cases the analyzer or the
      judge could not produce output for. These are surfaced separately and
      excluded from the quality fractions below, so an infrastructure hiccup
      doesn't masquerade as a quality regression.
    - ``category_accuracy`` — of the cases the analyzer actually diagnosed, the
      fraction whose category matched the expected one. Computed in code, not by
      the judge.
    - ``pass_rates`` — of the judged cases, the fraction the judge passed on each
      dimension (correctness/groundedness/completeness/actionability) plus
      ``overall`` (passed all four). This is the headline quality score: one number per dimension
      that you can compare across runs to see if a prompt/model change made the
      analyzer better or worse.

    :param records: The fully judged records.
    :returns: The ``summary`` dict embedded in the report and printed to console.
    """
    # Denominators: only cases that got a diagnosis / a judgement count toward
    # the corresponding quality fractions.
    diagnosed = [r for r in records if not r["scout_failure"]]
    judged = [r for r in records if r.get("judge")]

    def fraction(numerator: int, pool: list) -> float:
        """Safe count/total ratio rounded to 3 dp; 0.0 when the pool is empty."""
        return round(numerator / len(pool), 3) if pool else 0.0

    # How many judged cases the judge passed on each dimension
    pass_rates = {
        dim: fraction(sum(1 for r in judged if r["judge"][dim]["verdict"] == "pass"), judged)
        for dim in DIMENSIONS
    }
    pass_rates["overall"] = fraction(sum(1 for r in judged if r["overall_pass"]), judged)

    return {
        "total_cases": len(records), # Every record, including failures.
        "judged_cases": len(judged), # Size of the judged pool
        "scout_failures": sum(1 for r in records if r["scout_failure"]), # Count over all records where the analyzer produced nothing
        "judge_errors": sum(1 for r in records if r.get("judge_error")), # Count where the judge failed
        "category_accuracy": fraction(sum(1 for r in diagnosed if r["category_match"]), diagnosed), # Fraction of diagnosed cases whose category matched
        "pass_rates": pass_rates, # The per-dimension + overall dict built above
    }


def _print_table(records: list[dict], summary: dict) -> None:
    """
    Print the per-case table and the aggregate summary to the console.

    One row per case showing expected→diagnosed category (with a ✓/✗ match
    mark) and the four per-dimension verdicts, followed by the counts and
    pass-rate percentages from :func:`_summarize`.

    :param records: The fully judged records.
    :param summary: The summary dict from :func:`_summarize`.
    """

    def verdict(record, dim):
        """Cell text for one dimension: the judge verdict, or an error marker if there's no judgement."""
        if record["scout_failure"]:
            return "SCOUT-ERR"
        if record.get("judge_error") or not record.get("judge"):
            return "JUDGE-ERR"
        return record["judge"][dim]["verdict"]

    header = f"{'case_id':<28} {'category (expected→got)':<34} {'corr':<5} {'grnd':<5} {'cmpl':<5} {'actn':<5} {'overall'}"
    print("\n" + header)
    print("-" * len(header))
    for r in records:
        got = "—" if r["scout_failure"] else (r["diagnosis"].get("category") or "?")
        cat = f"{r['expected_category']}→{got}"
        mark = "✓" if r.get("category_match") else "✗"
        overall = "PASS" if r.get("overall_pass") else "FAIL"
        print(
            f"{r['case_id']:<28} {cat:<32}{mark:>2} "
            f"{verdict(r, 'correctness'):<5} {verdict(r, 'groundedness'):<5} "
            f"{verdict(r, 'completeness'):<5} {verdict(r, 'actionability'):<5} {overall}"
        )

    pr = summary["pass_rates"]
    print(
        f"\nCases: {summary['total_cases']}  judged: {summary['judged_cases']}  "
        f"scout_failures: {summary['scout_failures']}  judge_errors: {summary['judge_errors']}"
    )
    print(f"Category accuracy: {summary['category_accuracy']:.0%}")
    print(
        f"Pass rates — correctness: {pr['correctness']:.0%}  "
        f"groundedness: {pr['groundedness']:.0%}  completeness: {pr['completeness']:.0%}  "
        f"actionability: {pr['actionability']:.0%}  overall: {pr['overall']:.0%}\n"
    )


def main(argv=None) -> int:
    """
    Entry point: diagnose every dataset case, judge each diagnosis, report.

    The orchestrator that Loads the dataset, runs the analyzer over it, judges the results, writes the
    JSON report, and prints the summary table.

    The shape of it: It does no analysis or grading itself, it just sequences the named stages and handles the I/O
    boundary (args in, env check, file out, exit code out). Three things stand out as intentional: the early fail-fast
    on the missing key (exit 2 before any work), the single shared records list threaded through
    produce→grade→aggregate, and the three distinct exit codes that let a caller distinguish can't-run / failed / passed

    :param argv: Optional argument list (defaults to ``sys.argv``).
    :returns: Process exit code — ``0`` if every judged case passed all four
        dimensions, ``1`` if any failed, ``2`` if ``GROQ_API_KEY`` is missing.
    """
    load_dotenv()
    parser = argparse.ArgumentParser(prog="python -m evals", description=__doc__)
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="golden dataset YAML")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="results JSON path")
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL, help="Groq model id for the judge")
    args = parser.parse_args(argv)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY is not set (needed for both the analyzer and the judge).", file=sys.stderr)
        return 2

    cases = load_dataset(args.dataset)
    cases_by_id = {c["id"]: c for c in cases}

    # The heart of the run
    records = _diagnose_cases(cases) # Produce
    _judge_records(records, cases_by_id, model=args.judge_model, api_key=api_key) # Grade
    summary = _summarize(records) # Aggregate

    scout_model = _make_scout().model
    # Assemble report
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "dataset": args.dataset,
        "scout_model": scout_model,
        "judge_model": args.judge_model,
        "summary": summary,
        "cases": records,
    }

    # Build Report
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    _print_table(records, summary)
    print(f"Report written to {out_path}")

    return 0 if summary["pass_rates"]["overall"] >= 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())