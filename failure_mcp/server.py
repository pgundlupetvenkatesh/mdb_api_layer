"""
MCP server entry point for mdb_api_layer.

Registers all tools from :mod:`failure_mcp.tools.analyze_test_failure` and starts
the server on the stdio transport (default for local MCP clients).

The server exposes the following tools to any MCP-compatible AI client
(Claude Desktop, Cursor, VS Code Copilot Chat, etc.):

- :func:`analyze_failure <failure_mcp.tools.analyze_test_failure.handle_call>` —
  run LLM diagnosis on a single test failure.
- :func:`get_results <failure_mcp.tools.analyze_test_failure.handle_call>` —
  return accumulated results filtered by minimum confidence.
- :func:`save_results <failure_mcp.tools.analyze_test_failure.handle_call>` —
  flush results to ``failure_analysis.json``.

Usage::

    poetry run python -m failure_mcp.server

MCP client config example (``~/.cursor/mcp.json`` or Claude Desktop settings)::

    {
      "mcpServers": {
        "failure-analyzer": {
          "command": "poetry",
          "args": ["run", "python", "-m", "failure_mcp.server"],
          "cwd": "/path/to/mdb_api_layer",
          "env": {
            "AI_ANALYSIS_ENABLED": "true",
            "GROQ_API_KEY": "<your-key>"
          }
        }
      }
    }

.. module:: failure_mcp.server
   :synopsis: MCP server bootstrap for AI-powered test failure analysis.
"""

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server

from failure_mcp.tools.analyze_test_failure import TOOLS, handle_call

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

#: The :class:`mcp.server.Server` instance named ``"failure-analyzer"``.
#: Decorated handler functions below are registered against this instance.
app = Server("failure-analyzer")


@app.list_tools()
async def list_tools():
    """Advertise all available tools to the connecting MCP client.

    Called automatically by the MCP protocol during the handshake phase.
    Returns the static :data:`~failure_mcp.tools.analyze_test_failure.TOOLS`
    list defined in the tools module so that tool definitions are maintained
    in one place.

    :returns: List of :class:`mcp.types.Tool` objects — one entry per
        exposed capability (``analyze_failure``, ``get_results``,
        ``save_results``).
    """
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Receive and forward a tool invocation from the MCP client.

    Acts as a thin router: every tool call that arrives over the stdio
    transport is immediately delegated to
    :func:`~failure_mcp.tools.analyze_test_failure.handle_call`, which
    contains the actual dispatch logic and calls into the
    :class:`~tests.helpers.failure_analyzer.FailureAnalyzer` singleton.

    :param name: Tool name as sent by the MCP client. Expected values are
        ``"analyze_failure"``, ``"get_results"``, or ``"save_results"``.
    :param arguments: Dict of arguments validated by the client against the
        JSON Schema advertised in :func:`list_tools`.
    :returns: List of :class:`mcp.types.TextContent` with the JSON result,
        as returned by :func:`~failure_mcp.tools.analyze_test_failure.handle_call`.
    :raises ValueError: Propagated from ``handle_call`` if ``name`` is unknown.
    """
    return await handle_call(name, arguments)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def _serve():
    """Start the MCP server and block until the client disconnects.

    Opens the stdio streams provided by the MCP runtime and hands them to
    :meth:`mcp.server.Server.run`, which drives the JSON-RPC message loop.
    Initialization options are generated from the server's registered
    capabilities (tools in this case).

    Called by the ``__main__`` block; not intended to be called directly.
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(_serve())
