MCP Server (failure_mcp)
========================

Exposes :class:`~tests.helpers.failure_analyzer.FailureAnalyzer` capabilities
as callable tools over the `Model Context Protocol (MCP) <https://modelcontextprotocol.io/>`_
stdio transport. Compatible with Claude Desktop, Cursor, VS Code Copilot Chat,
and any other MCP-compatible AI client.

Server
------
.. automodule:: failure_mcp.server
   :members:
   :undoc-members:
   :show-inheritance:

Tools
-----
.. automodule:: failure_mcp.tools.analyze_test_failure
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:
