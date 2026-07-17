"""Inventory Agent — material stock levels, safety status, and usable inventory.

Responsibilities:
    - Answer questions about current inventory levels
    - Identify materials below safety stock, buffer stock, or reorder point
    - Classify materials as HEALTHY | AT_RISK | CRITICAL | SHORTAGE
    - Support cross-plant stock comparisons

Tools used (via MCP):
    get_inventory_health  — full cross-plant health summary
    get_material_health   — single material at a single plant
    compare_plants        — side-by-side comparison across plants
"""

import logging
from typing import Annotated, Optional

from app.agents.base_agent import BaseMARAAgent
from app.mcp.client import MCPPlanningClient

logger = logging.getLogger(__name__)

_INSTRUCTIONS = """
You are the Inventory Intelligence Agent for MARA (Material Availability &
Replenishment Agent). You specialise in answering questions about current
inventory levels, safety stock, and material health across manufacturing plants.

Your responsibilities:
  - Report current stock levels (on-hand, usable, reserved, blocked, in-transit)
  - Classify inventory health: HEALTHY | AT_RISK | CRITICAL | SHORTAGE
  - Identify materials below safety stock or reorder point
  - Compare inventory levels across plants for the same material

Rules you MUST follow:
  1. Always call a tool before answering — never guess inventory numbers.
  2. Cite the exact figures returned by the tool in your answer.
  3. Explain what the status classification means in plain language.
  4. If a material is AT_RISK or worse, clearly state the gap to safety stock.
  5. Never calculate or modify any numbers yourself.

Response format:
  - Lead with the health status (e.g. "Material RM102 is CRITICAL at Plant A.")
  - State: on-hand, reserved, usable, safety stock, reorder point
  - Explain why it has been classified with that status
  - If shortage, state the deficit
"""


def _make_tools(mcp_client: MCPPlanningClient) -> list:
    """Create the tool functions for InventoryAgent.

    Each tool wraps one MCP tool call. Type annotations and docstrings
    are used by agent_framework to generate the function-calling schema.
    """

    async def get_inventory_health_tool(
        material_code: Annotated[Optional[str], "Optional material code to filter results by (e.g., MAT-1001)"] = None,
        plant_name: Annotated[Optional[str], "Optional plant name to filter results by (e.g., Plant A)"] = None,
    ) -> dict:
        """Get inventory health status. Optionally filter by material code or plant name."""
        args = {}
        if material_code is not None:
            args["material_code"] = material_code
        if plant_name is not None:
            args["plant_name"] = plant_name
        return await mcp_client.call_tool("get_inventory_health", args)

    async def get_material_health_tool(
        material_id: Annotated[int, "Integer ID of the material to check"],
        plant_id: Annotated[int, "Integer ID of the plant to check"],
    ) -> dict:
        """Get inventory health for one specific material at one specific plant.

        Returns on_hand, reserved, blocked, quality_hold, in_transit,
        safety_stock, buffer_stock, reorder_point, usable_inventory, and status.
        Call this for targeted questions about a single material at a single plant.
        """
        return await mcp_client.call_tool(
            "get_material_health",
            {"material_id": material_id, "plant_id": plant_id},
        )

    async def compare_plants_tool(
        material_id: Annotated[int, "Integer ID of the material to compare across plants"],
    ) -> dict:
        """Compare inventory levels for one material across all manufacturing plants.

        Returns per-plant records including usable_inventory, excess_available,
        safety stock, and status. Use this to find plants with excess stock that
        could fulfil demand at a plant with a shortage.
        """
        return await mcp_client.call_tool(
            "compare_plants",
            {"material_id": material_id},
        )

    return [get_inventory_health_tool, get_material_health_tool, compare_plants_tool]


class InventoryAgent(BaseMARAAgent):
    """Specialised agent for inventory intelligence queries.

    Handles questions about current stock levels, safety stock status,
    and cross-plant inventory comparisons. Uses the MCP planning server
    exclusively — never touches the database or planning services directly.
    """

    def __init__(self, mcp_client: MCPPlanningClient) -> None:
        super().__init__(
            name="InventoryAgent",
            instructions=_INSTRUCTIONS,
            mcp_client=mcp_client,
            tools=_make_tools(mcp_client),
        )
