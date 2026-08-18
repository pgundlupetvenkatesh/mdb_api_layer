Evaluation Harness (evals)
==========================

LLM-as-a-judge evaluation of the AI failure analyzer's diagnosis quality.
Runs :class:`~tests.helpers.failure_analyzer.FailureAnalyzer` (Qwen3.6 27B via
Groq) over a curated golden dataset, then scores each diagnosis with a separate
judge model (``openai/gpt-oss-120b`` by default — a different model family, so
no self-preference). Run with ``poetry run python -m evals``.

Dataset
-------
.. automodule:: evals.dataset
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:

Judge
-----
.. automodule:: evals.judge
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:

CLI Runner
----------
.. automodule:: evals.__main__
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members: