"""Replenishment Agent — replenishment recommendations and cross-plant transfers.

Responsibilities:
    - Generate and explain replenishment recommendations
    - Identify cross-plant transfer opportunities
    - Report dashboard KPIs
    - Recommend actions: Expedite PO | Transfer | New PO | Restore Safety Stock

Tools used (via MCP):
    recommend_replenishment — 4-rule priority engine output
    compare_plants          — excess stock across plants for one material
    get_dashboard_kpis      — high-level planning summary
    explain_recommendation  — full evidence for a specific recommendation
"""

import logging
from typing import Annotated, Optional

from app.agents.base_agent import BaseMARAAgent
from app.mcp.client import MCPPlanningClient

logger = logging.getLogger(__name__)

_INSTRUCTIONS = """
You are the Replenishment Agent for MARA (Material Availability &
Replenishment Agent). You specialise in generating, explaining, and
prioritising supply replenishment actions.

Your responsibilities:
  - Present replenishment recommendations with their evidence and confidence
  - Explain the business rule that triggered each recommendation
  - Identify cross-plant transfer opportunities before new procurement
  - Summarise planning dashboard KPIs on request

Rules you MUST follow:
  1. Always call a tool before answering — never invent recommendations.
  2. Cite the exact evidence: shortage date, deficit qty, excess plant, PO numbers.
  3. Present recommendations in priority order: CRITICAL → HIGH → MEDIUM → LOW.
  4. For transfers, state source plant, destination plant, quantity, and ETA.
  5. For new POs, state: quantity, suggested order date, ETA (lead time).
  6. Never calculate or modify any numbers yourself.

Response format:
  - State the total number of recommendations (e.g. "5 replenishment actions found.")
  - Group by priority: CRITICAL first
  - For each: type | material | plant | quantity | ETA | confidence | reason
  - For dashboard KPIs: present as a clear summary with labels
"""


def _make_tools(mcp_client: MCPPlanningClient) -> list:
    """Create tool functions for ReplenishmentAgent."""

    async def recommend_replenishment_tool() -> dict:
        """Generate evidence-backed replenishment recommendations.

        Applies a 4-rule priority engine:
          1. Expedite Existing Late PO
          2. Transfer Stock Between Plants
          3. Create New Purchase Order
          4. Restore Safety Stock

        Returns recommendations with: type, quantity, priority, confidence,
        reason, evidence, eta_date, source_plant (for transfers).
        Call this for all replenishment action questions.
        """
        return await mcp_client.call_tool("recommend_replenishment")

    async def compare_plants_tool(
        material_id: Annotated[
            int, "Integer ID of the material to compare across plants"
        ],
    ) -> dict:
        """Compare inventory levels for one material across all plants.

        Returns per-plant: usable_inventory, excess_available, safety_stock, status.
        Use this to identify if a cross-plant transfer is feasible before
        recommending a new purchase order.
        """
        return await mcp_client.call_tool(
            "compare_plants", {"material_id": material_id}
        )

    async def get_dashboard_kpis_tool() -> dict:
        """Return high-level planning dashboard KPIs.

        Returns: total_materials, healthy/at_risk/critical/shortage counts,
        active_production_orders, open_purchase_orders,
        impacted_production_orders, safety_stock_violations, critical_shortages.
        Call this for summary overview questions.
        """
        return await mcp_client.call_tool("get_dashboard_kpis")

    async def explain_recommendation_tool(
        recommendation_id: Annotated[
            int, "Integer ID of the replenishment recommendation to explain"
        ],
    ) -> dict:
        """Retrieve the full evidence and justification for a recommendation.

        Returns: type, priority, confidence, reason, evidence, eta_date,
        material_code, plant_name, source_plant_name.
        Call this when asked to explain why a specific recommendation was made.
        """
        return await mcp_client.call_tool(
            "explain_recommendation", {"recommendation_id": recommendation_id}
        )

    return [
        recommend_replenishment_tool,
        compare_plants_tool,
        get_dashboard_kpis_tool,
        explain_recommendation_tool,
    ]


class ReplenishmentAgent(BaseMARAAgent):
    """Specialised agent for replenishment decisions and planning summaries.

    Handles questions about what supply actions to take, cross-plant
    transfer feasibility, and planning dashboard overviews.
    """

    def __init__(self, mcp_client: MCPPlanningClient) -> None:
        super().__init__(
            name="ReplenishmentAgent",
            instructions=_INSTRUCTIONS,
            mcp_client=mcp_client,
            tools=_make_tools(mcp_client),
        )
