"""Production Agent — production order risk, BOM-based shortage impact, and projections.

Responsibilities:
    - Identify production orders blocked by component shortages
    - Compute time-phased availability projections
    - Explain BOM explosion results and component deficits
    - Report shortage timelines: first shortage date, days of coverage, recovery date

Tools used (via MCP):
    analyze_production_impact  — orders blocked by BOM component shortages
    calculate_projection       — time-phased projected balance
"""

import logging
from typing import Annotated, Optional

from app.agents.base_agent import BaseMARAAgent
from app.mcp.client import MCPPlanningClient

logger = logging.getLogger(__name__)

_INSTRUCTIONS = """
You are the Production Impact Agent for MARA (Material Availability &
Replenishment Agent). You specialise in assessing which production orders are
at risk due to material shortages and in projecting future material availability.

Your responsibilities:
  - Identify production orders that cannot proceed due to insufficient components
  - Run time-phased projections to show when shortages will occur
  - Explain BOM explosion results: which component is short, by how much
  - Report first shortage date, days of coverage, and projected recovery date

Rules you MUST follow:
  1. Always call a tool before answering — never guess production or shortage data.
  2. Cite exact figures: order numbers, component codes, required vs available qty.
  3. For projections, state the initial balance, the first shortage date, and deficit.
  4. If no orders are impacted, explicitly confirm production is safe.
  5. Never calculate or modify any numbers yourself.

Response format:
  - State how many production orders are at risk (e.g. "3 production orders are at risk.")
  - For each impacted order: order number, material, plant, required date, priority
  - For each shortage: component code, required qty, available qty, deficit
  - For projections: initial balance → shortage date → deficit quantity
"""


def _make_tools(mcp_client: MCPPlanningClient) -> list:
    """Create tool functions for ProductionAgent."""

    async def analyze_production_impact_tool(
        plant_id: Annotated[
            Optional[int],
            "Optional plant ID to filter results. Pass None to check all plants.",
        ] = None,
    ) -> dict:
        """Identify all production orders at risk due to component shortages.

        Performs BOM explosion for every active production order and checks
        whether all required components have sufficient usable inventory.
        Returns impacted orders with shortage breakdowns per component.
        Call this to find which production orders cannot proceed.
        """
        args = {}
        if plant_id is not None:
            args["plant_id"] = plant_id
        return await mcp_client.call_tool("analyze_production_impact", args)

    async def calculate_projection_tool(
        material_id: Annotated[int, "Integer ID of the material to project"],
        plant_id: Annotated[int, "Integer ID of the plant to project"],
        horizon_days: Annotated[
            int, "Number of days to project forward (7 to 90)"
        ] = 30,
    ) -> dict:
        """Calculate a time-phased material availability projection.

        Uses the formula: Balance = Previous Balance + Incoming Supply - Production Demand.
        Returns: initial_balance, first_shortage_date, shortage_quantity,
        days_of_coverage, recovery_date, and a day-by-day timeline.
        Call this to answer shortage timeline questions.
        """
        return await mcp_client.call_tool(
            "calculate_projection",
            {
                "material_id": material_id,
                "plant_id": plant_id,
                "horizon_days": horizon_days,
            },
        )

    return [analyze_production_impact_tool, calculate_projection_tool]


class ProductionAgent(BaseMARAAgent):
    """Specialised agent for production impact and material projection queries.

    Handles questions about which production orders are blocked, when shortages
    will occur, and what the component-level deficits are.
    """

    def __init__(self, mcp_client: MCPPlanningClient) -> None:
        super().__init__(
            name="ProductionAgent",
            instructions=_INSTRUCTIONS,
            mcp_client=mcp_client,
            tools=_make_tools(mcp_client),
        )
