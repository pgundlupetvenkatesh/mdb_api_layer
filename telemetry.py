"""
Process-wide token/cost ledger for the AI failure-analysis pipeline.

Every Groq response carries a ``usage`` block (prompt/completion/total tokens)
that the analyzer and judge would otherwise discard. Both call sites record it
here via :meth:`TokenLedger.record`; ``conftest.py`` drains the ledger at
session end, rolls it up into one run-level row (tokens + estimated cost +
quality), and appends it to ``ai_analysis/token_usage.jsonl`` for cross-run
trending.

Tokens are the durable, provider-independent signal; the dollar figure is a
derived estimate from a small, dated price table and is best-effort only — a
model missing from the table contributes 0 to the cost estimate but its tokens
are still counted. Recording is defensive: a malformed ``usage`` object can
never raise into a test run.

.. module:: telemetry
   :synopsis: Token/cost ledger for the LLM failure-analysis pipeline.
   :no-index:
"""

from dataclasses import dataclass

# USD per 1,000,000 tokens, keyed by Groq model id, as ``(input, output)``.
# Dated table (2026-09, Groq published pricing) — prices drift, so this is the
# one place to update. A model absent here is still token-counted; it just
# contributes 0 to est_cost_usd.
_PRICE_PER_MILLION: dict[str, tuple[float, float]] = {
    "qwen/qwen3.8-27b": (0.80, 4.00),
    "qwen/qwen3.6-27b": (0.60, 3.00),  # deprecated on Groq; kept for pinned AI_MODEL runs
    "llama-3.3-70b-versatile": (0.59, 0.79),  # deprecated on Groq; kept for pinned AI_MODEL runs
    "openai/gpt-oss-120b": (0.15, 0.75),
}


@dataclass
class _Record:
    """One recorded LLM call's token usage."""

    model: str
    role: str  # analyze | refine | judge
    prompt_tokens: int
    completion_tokens: int
    test_name: str


class TokenLedger:
    """
    Accumulates per-call token usage for one pytest session.

    A single process-wide instance (:data:`ledger`) is shared by the analyzer
    and the judge; ``conftest.py`` reads it once at session end. Not
    thread-safe — the pipeline runs calls serially per test.
    """

    def __init__(self):
        self._records: list[_Record] = []

    def record(self, *, model: str, role: str, usage, test_name: str = "unknown") -> None:
        """
        Record one LLM call's token usage from a Groq ``response.usage`` object.

        Defensive by design: a ``None`` or malformed ``usage`` counts as zero
        tokens rather than raising, so telemetry can never break a test run.

        :param model: The Groq model id that served the call.
        :param role: Which pipeline step spent the tokens
            (``analyze`` | ``refine`` | ``judge``).
        :param usage: The Groq ``CompletionUsage`` object (``response.usage``);
            ``prompt_tokens`` / ``completion_tokens`` are read off it.
        :param test_name: The failed test this call was diagnosing.
        """
        try:
            prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
            completion = int(getattr(usage, "completion_tokens", 0) or 0)
        except (TypeError, ValueError):
            prompt = completion = 0
        self._records.append(_Record(model, role, prompt, completion, test_name))

    @property
    def records(self) -> list[_Record]:
        """All calls recorded this session (read-only view)."""
        return self._records

    def reset(self) -> None:
        """Drop all recorded calls (used by tests to isolate runs)."""
        self._records.clear()

    def estimate_cost_usd(self) -> float:
        """
        Best-effort dollar estimate for all recorded calls.

        ``cost = Σ (prompt_tokens × in_price + completion_tokens × out_price)``
        from :data:`_PRICE_PER_MILLION`. Calls whose model is not in the price
        table contribute 0.

        :returns: Estimated cost in USD, rounded to 6 decimals. Example return
            for 1000 prompt + 200 completion tokens on qwen/qwen3.8-27b
            (``1000/1e6 * 0.80 + 200/1e6 * 4.00``)::

                0.0016
        """
        total = 0.0
        for r in self._records:
            price = _PRICE_PER_MILLION.get(r.model)
            if not price:
                continue
            in_price, out_price = price
            total += r.prompt_tokens / 1e6 * in_price + r.completion_tokens / 1e6 * out_price
        return round(total, 6)

    def summary(self) -> dict:
        """
        Roll the recorded calls up into a run-level totals dict.

        :returns: ``{calls, prompt_tokens, completion_tokens, total_tokens,
            est_cost_usd}`` — the token/cost half of the JSONL trend row. Example::

                {"calls": 5, "prompt_tokens": 8421, "completion_tokens": 1290,
                 "total_tokens": 9711, "est_cost_usd": 0.0021}
        """
        prompt = sum(r.prompt_tokens for r in self._records)
        completion = sum(r.completion_tokens for r in self._records)
        return {
            "calls": len(self._records),
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": prompt + completion,
            "est_cost_usd": self.estimate_cost_usd(),
        }


# Singleton instance — shared across the analyzer and judge for one session.
ledger = TokenLedger()