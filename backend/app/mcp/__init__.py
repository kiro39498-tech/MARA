"""MARA MCP Package.

Contains:
    server.py  — FastMCP server that exposes all planning capabilities as MCP tools.
    client.py  — MCPPlanningClient used by agents to call the MCP server.

Architecture rule:
    Planning Services → MCP Server (server.py)
    MCP Server ← MCP Client (client.py) ← Agents
    Agents NEVER import Planning Services directly.
"""
