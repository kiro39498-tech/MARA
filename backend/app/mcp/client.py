"""MCP Planning Client.

Used exclusively by MARA agents to call tools on the MCP Planning Server.

Architecture rules enforced here:
    ✅ Agents call planning tools ONLY through this client.
    ✅ This client speaks JSON-RPC 2.0 over streamable-http transport.
    ❌ Agents must NEVER import Planning Services directly.
    ❌ This client must NEVER contain business logic.
"""

import json
import logging
import uuid
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class MCPPlanningClient:
    """Async HTTP client for the MARA MCP Planning Server.

    Speaks JSON-RPC 2.0 over the streamable-http MCP transport.
    All agent tool calls route through this client.

    Usage:
        client = MCPPlanningClient(base_url="http://127.0.0.1:8001")
        result = await client.call_tool("get_inventory_health")
        result = await client.call_tool("calculate_projection", {
            "material_id": 1, "plant_id": 1, "horizon_days": 30
        })
        await client.close()

    Context manager usage:
        async with MCPPlanningClient(base_url=...) as client:
            result = await client.call_tool("get_dashboard_kpis")
    """

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        """Initialise the MCP client.

        Args:
            base_url: Base URL of the MCP Planning Server (e.g. http://127.0.0.1:8001).
            timeout:  HTTP request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout)
        # MCP streamable-http endpoint
        self._mcp_endpoint = f"{self.base_url}/mcp"

    # ------------------------------------------------------------------
    # Core JSON-RPC 2.0 method
    # ------------------------------------------------------------------

    async def _jsonrpc(
        self, method: str, params: Optional[dict] = None
    ) -> Any:
        """Send a JSON-RPC 2.0 request and return the result.

        Args:
            method: JSON-RPC method name (e.g. "tools/call", "tools/list").
            params: Optional parameters dict.

        Returns:
            The "result" field from the JSON-RPC response.

        Raises:
            httpx.HTTPStatusError: On non-2xx HTTP responses.
            ValueError: On JSON-RPC error responses.
        """
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": request_id,
        }

        logger.debug("MCP → %s params=%s", method, params)

        response = await self._client.post(
            self._mcp_endpoint,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        response.raise_for_status()

        # The MCP streamable-http transport may return plain JSON or SSE.
        # We handle both here.
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            # Parse the first "data:" line from the SSE stream
            body = _parse_sse_first_event(response.text)
        else:
            body = response.json()

        logger.debug("MCP ← %s", body)

        # JSON-RPC error check
        if "error" in body:
            err = body["error"]
            raise ValueError(
                f"MCP tool error [{err.get('code', 'unknown')}]: {err.get('message', str(err))}"
            )

        return body.get("result")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def call_tool(
        self, tool_name: str, arguments: Optional[dict[str, Any]] = None
    ) -> Any:
        """Call a named tool on the MCP Planning Server.

        Args:
            tool_name:  Name of the MCP tool (e.g. "get_inventory_health").
            arguments:  Tool input parameters as a dict. Defaults to {}.

        Returns:
            The tool's return value (typically a dict with "success" and "data" keys).
        """
        result = await self._jsonrpc(
            method="tools/call",
            params={"name": tool_name, "arguments": arguments or {}},
        )
        # FastMCP wraps the tool return value inside {"content": [{"text": ...}]}
        # Unwrap it so agents always receive the raw dict.
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and content:
                first = content[0]
                if isinstance(first, dict) and first.get("type") == "text":
                    try:
                        return json.loads(first["text"])
                    except (json.JSONDecodeError, KeyError):
                        return first.get("text", result)
        return result

    async def list_tools(self) -> list[dict]:
        """List all tools exposed by the MCP Planning Server.

        Returns:
            List of tool descriptors: [{name, description, inputSchema}, ...]
        """
        result = await self._jsonrpc(method="tools/list")
        if isinstance(result, dict):
            return result.get("tools", [])
        return result or []

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        await self._client.aclose()

    async def __aenter__(self) -> "MCPPlanningClient":
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_sse_first_event(text: str) -> dict:
    """Extract the first JSON payload from an SSE response body.

    SSE events look like:
        event: message
        data: {"jsonrpc": "2.0", "result": {...}, "id": "..."}

    Returns the parsed JSON dict from the first "data:" line.
    """
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            data_str = line[len("data:"):].strip()
            try:
                return json.loads(data_str)
            except json.JSONDecodeError:
                pass
    # Fallback — try the raw text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": {"code": -1, "message": f"Unparseable response: {text[:200]}"}}
