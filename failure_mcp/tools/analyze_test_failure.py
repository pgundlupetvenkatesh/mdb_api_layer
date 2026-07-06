"""
MCP tool definitions for AI-powered test failure analysis.

Exposes three tools:

- ``analyze_failure`` — send a failure context to the LLM and get a structured diagnosis.
- ``get_results``     — retrieve accumulated diagnosis results (with optional confidence filter).
- ``save_results``    — flush all results to ``<output_dir>/failure_analysis.json``.

This module is imported by ``failure_mcp/server.py``, which registers the handlers
on the :class:`mcp.server.Server` instance.

Tool Schemas
------------
Each entry in :data:`TOOLS` is a :class:`mcp.types.Tool` that carries:

- ``name``        — identifier used by the MCP client when calling the tool.
- ``description`` — human-readable summary shown in the client UI.
- ``inputSchema`` — JSON Schema object describing required and optional arguments.

.. module:: failure_mcp.tools.analyze_test_failure
   :synopsis: MCP tool definitions wrapping FailureAnalyzer.
   :no-index:
"""

import json
from typing import Any

from mcp import types

# Import the singleton — failure_analyzer.py is NOT modified. The whole point is to expose the object's methods without
# modifying it.
from tests.helpers.failure_analyzer import analyzer


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

#: List of :class:`mcp.types.Tool` objects advertised to MCP clients.
#:
#: Contains three tools:
#:
#: ``analyze_failure``
#:     Required args: ``test_name``, ``error_message``.
#:     Optional args: ``test_file``, ``traceback``, ``api_url``, ``status_code``,
#:     ``response_body``.
#:
#: ``get_results``
#:     Optional arg: ``min_confidence`` (int 0–100, default 0).
#:
#: ``save_results``
#:     Optional arg: ``output_dir`` (str, default ``"ai_analysis"``).
TOOLS: list[types.Tool] = [
    types.Tool(
        name="analyze_failure",
        description=(
            "Send a test failure context to the LLM and receive a structured "
            "diagnosis with root_cause, category, suggested_fix, confidence (0-100 %), "
            "explanation, evidence, and a human-readable confidence_tier."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "test_name": {
                    "type": "string",
                    "description": "Name of the failed test function."
                },
                "test_file": {
                    "type": "string",
                    "description": "Relative path to the test file."
                },
                "error_message": {
                    "type": "string",
                    "description": "The assertion or exception message."
                },
                "traceback": {
                    "type": "string",
                    "description": "Full traceback string."
                },
                "api_url": {
                    "type": "string",
                    "description": "The API URL that was called (optional)."
                },
                "status_code": {
                    "type": "integer",
                    "description": "HTTP status code received (optional)."
                },
                "response_body": {
                    "type": "string",
                    "description": "API response body or snippet (optional)."
                }
            },
            "required": ["test_name", "error_message"]
        }
    ),
    types.Tool(
        name="get_results",
        description=(
            "Return all diagnosis results accumulated during this MCP server "
            "session as a JSON array. Optionally filter by minimum confidence."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "min_confidence": {
                    "type": "integer",
                    "description": "Only return results with confidence >= this value (0–100). Defaults to 0.",
                    "default": 0
                }
            },
            "required": []
        }
    ),
    types.Tool(
        name="save_results",
        description=(
            "Flush all accumulated diagnosis results to "
            "<output_dir>/failure_analysis.json. "
            "Returns the number of results written and the output path."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "output_dir": {
                    "type": "string",
                    "description": "Directory to write failure_analysis.json. Defaults to 'ai_analysis'.",
                    "default": "ai_analysis"
                }
            },
            "required": []
        }
    )
]


# ---------------------------------------------------------------------------
# Call dispatcher
# ---------------------------------------------------------------------------

def _confidence_tier(score: int) -> str:
    """A pure helper def: Map a 0–100 confidence score the LLM returns to a human-readable tier label.

    Used to attach a ``confidence_tier`` field alongside the raw numeric ``confidence`` value in the ``analyze_failure``
    response, so MCP clients can display or filter results without implementing their own thresholds. This will enrich
    the diagnosis before returning it to the client without modifying
    :py:class:`tests.helpers.failure_analyzer.FailureAnalyzer`.

    Thresholds:

    +----------+-----------+
    | Range    | Tier      |
    +==========+===========+
    | >= 80    | ``high``  |
    +----------+-----------+
    | 50 – 79  | ``medium``|
    +----------+-----------+
    | < 50     | ``low``   |
    +----------+-----------+

    :param score: Integer confidence score (0–100) returned by the LLM.
    :returns: One of ``"high"``, ``"medium"``, or ``"low"``.

    Example::

        >>> _confidence_tier(92)
        'high'
        >>> _confidence_tier(65)
        'medium'
        >>> _confidence_tier(30)
        'low'
    """
    if score >= 80:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


async def handle_call(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Dispatch an MCP tool call to the appropriate :class:`FailureAnalyzer` method.

    Called by ``failure_mcp/server.py``'s ``call_tool`` hook for every tool
    invocation arriving from the MCP client. Delegates to the
    :data:`~tests.helpers.failure_analyzer.analyzer` singleton without
    modifying ``failure_analyzer.py``.

    **Tool behavior:**

    ``analyze_failure``
        Calls :meth:`~tests.helpers.failure_analyzer.FailureAnalyzer.analyze`
        with the supplied ``arguments`` dict as the ``failure_context``.
        On success, enriches the diagnosis with a ``confidence_tier`` field.
        On failure or when analysis is disabled, returns an ``error`` and
        ``hint`` dict instead.

    ``get_results``
        Reads :attr:`~tests.helpers.failure_analyzer.FailureAnalyzer._results`
        and filters entries whose ``confidence`` is >= ``min_confidence``
        (defaults to ``0``, i.e. return everything).

    ``save_results``
        Calls :meth:`~tests.helpers.failure_analyzer.FailureAnalyzer.save_results`
        with the given ``output_dir`` (defaults to ``"ai_analysis"``), then
        returns the count of results written and the output file path.

    :param name: Tool name requested by the MCP client. Must be one of
        ``"analyze_failure"``, ``"get_results"``, or ``"save_results"``.
    :param arguments: Key/value arguments supplied by the MCP client,
        validated against the JSON Schema in :data:`TOOLS`.
    :returns: A single-element list of :class:`mcp.types.TextContent` whose
        ``text`` field contains the JSON-serialized result (2-space indent).
    :raises ValueError: If ``name`` does not match any registered tool.

    Example response for ``analyze_failure``::

        {
          "root_cause": "...",
          "category": "auth_error",
          "suggested_fix": "...",
          "confidence": 92,
          "explanation": "...",
          "evidence": ["HTTP 401", "Response: Invalid API key"],
          "test_name": "test_get_movie_details",
          "model": "llama-3.3-70b-versatile",
          "confidence_tier": "high"
        }
    """
    if name == "analyze_failure":
        diagnosis = analyzer.analyze(failure_context=arguments)

        # When `self.enabled == False`, return a friendly error
        if diagnosis is None:
            result = {
                "error": "Analysis disabled or failed.",
                "hint": "Set AI_ANALYSIS_ENABLED=true and GROQ_API_KEY in the environment."
            }
        else:
            confidence = diagnosis.get("confidence", 0)
            result = {**diagnosis, "confidence_tier": _confidence_tier(confidence)}

    elif name == "get_results":
        min_confidence = int(arguments.get("min_confidence", 0))
        result = [
            r for r in analyzer._results
            if r.get("confidence", 0) >= min_confidence
        ]

    elif name == "save_results":
        output_dir = arguments.get("output_dir", "ai_analysis")
        count = len(analyzer._results)
        analyzer.save_results(output_dir=output_dir)
        result = {"saved": count, "path": f"{output_dir}/failure_analysis.json"}

    else:
        raise ValueError(f"Unknown tool: {name}")

    # A human-readable output in the client UI.
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

