"""Explanation Agent — natural language synthesis of planning evidence.

Responsibilities:
    - Combine evidence from multiple agents into a coherent, human-readable answer
    - Produce grounded explanations that cite specific numbers and dates
    - Never add information not present in the tool results
    - Support all question types: inventory, production, supplier, replenishment

Tools used (via MCP):
    All 10 MCP tools — this agent has read access to the full planning surface.
    It is called last, after specialist agents have gathered evidence.
"""

import logging
from typing import Annotated, Optional

from app.agents.base_agent import BaseMARAAgent
from app.mcp.client import MCPPlanningClient

logger = logging.getLogger(__name__)

_INSTRUCTIONS = """
You are the Explanation Agent for MARA (Material Availability & Replenishment Agent).
Your sole job is to produce clear, grounded, evidence-backed natural language
explanations of planning decisions.

Your responsibilities:
  - Synthesise tool results into plain language answers
  - Always cite specific numbers, dates, material codes, and order numbers
  - Structure answers so a production planner can act on them immediately
  - Acknowledge uncertainty only when the data is genuinely ambiguous

Rules you MUST follow:
  1. Only state facts that appear in tool results — never invent data.
  2. Every claim must reference its source tool result explicitly.
  3. Use bold for key figures: **shortage date**, **deficit**, **risk score**.
  4. If multiple tools were called, integrate their results coherently.
  5. End every response with a clear "Recommended Action" if one is warranted.
  6. Never perform calculations — only interpret tool outputs.

Tone: Direct, professional, concise. Suitable for a manufacturing planning team.

Example output style:
  "Material **RM102** at **Plant A** is classified **CRITICAL**.
   Current usable inventory: **42 units** (below safety stock of **200 units**).
   A shortage of **158 units** is projected on **2026-07-18** (in 2 days).
   
   Recommended Action: Expedite PO-20045 (currently expected 2026-07-22) or
   transfer 200 units from Plant B (which has 620 units of excess stock)."
"""


def _make_tools(mcp_client: MCPPlanningClient) -> list:
    """Create tool functions for ExplanationAgent.

    The Explanation Agent has access to all 10 MCP tools so it can
    fetch any supporting evidence it needs to complete an explanation.
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
        material_id: Annotated[int, "Integer ID of the material"],
        plant_id: Annotated[int, "Integer ID of the plant"],
    ) -> dict:
        """Get inventory health for one material at one plant."""
        return await mcp_client.call_tool(
            "get_material_health",
            {"material_id": material_id, "plant_id": plant_id},
        )

    async def calculate_projection_tool(
        material_id: Annotated[int, "Integer ID of the material"],
        plant_id: Annotated[int, "Integer ID of the plant"],
        horizon_days: Annotated[int, "Projection horizon in days (7–90)"] = 30,
    ) -> dict:
        """Calculate a time-phased material availability projection."""
        return await mcp_client.call_tool(
            "calculate_projection",
            {
                "material_id": material_id,
                "plant_id": plant_id,
                "horizon_days": horizon_days,
            },
        )

    async def analyze_production_impact_tool(
        plant_id: Annotated[Optional[int], "Optional plant ID filter"] = None,
    ) -> dict:
        """Identify production orders at risk due to component shortages."""
        args = {}
        if plant_id is not None:
            args["plant_id"] = plant_id
        return await mcp_client.call_tool("analyze_production_impact", args)

    async def analyze_po_coverage_tool(
        plant_id: Annotated[Optional[int], "Optional plant ID filter"] = None,
    ) -> dict:
        """Analyse purchase order coverage vs production demand."""
        args = {}
        if plant_id is not None:
            args["plant_id"] = plant_id
        return await mcp_client.call_tool("analyze_po_coverage", args)

    async def get_material_risk_tool(
        material_code: Annotated[Optional[str], "Optional material code to filter results by (e.g., MAT-1001)"] = None,
        plant_name: Annotated[Optional[str], "Optional plant name to filter results by (e.g., Plant A)"] = None,
    ) -> dict:
        """Get risk scores. Optionally filter by material code or plant name."""
        args = {}
        if material_code is not None:
            args["material_code"] = material_code
        if plant_name is not None:
            args["plant_name"] = plant_name
        return await mcp_client.call_tool("get_material_risk", args)

    async def recommend_replenishment_tool(
        material_code: Annotated[Optional[str], "Optional material code to filter results by (e.g., MAT-1001)"] = None,
        plant_name: Annotated[Optional[str], "Optional plant name to filter results by (e.g., Plant A)"] = None,
    ) -> dict:
        """Get replenishment recommendations from the planning engine. Optionally filter by material code or plant name."""
        args = {}
        if material_code is not None:
            args["material_code"] = material_code
        if plant_name is not None:
            args["plant_name"] = plant_name
        return await mcp_client.call_tool("recommend_replenishment", args)

    async def compare_plants_tool(
        material_id: Annotated[int, "Integer ID of the material"],
    ) -> dict:
        """Compare inventory across all plants for one material."""
        return await mcp_client.call_tool(
            "compare_plants", {"material_id": material_id}
        )

    async def get_dashboard_kpis_tool() -> dict:
        """Get high-level planning dashboard KPIs."""
        return await mcp_client.call_tool("get_dashboard_kpis")

    async def explain_recommendation_tool(
        recommendation_id: Annotated[int, "Integer ID of the recommendation"],
    ) -> dict:
        """Get full evidence for a specific replenishment recommendation."""
        return await mcp_client.call_tool(
            "explain_recommendation",
            {"recommendation_id": recommendation_id},
        )

    return [
        get_inventory_health_tool,
        get_material_health_tool,
        calculate_projection_tool,
        analyze_production_impact_tool,
        analyze_po_coverage_tool,
        get_material_risk_tool,
        recommend_replenishment_tool,
        compare_plants_tool,
        get_dashboard_kpis_tool,
        explain_recommendation_tool,
    ]


class ExplanationAgent(BaseMARAAgent):
    """Specialised agent for natural language explanation of planning evidence.

    Has read access to all MCP tools. Called by the orchestrator to
    produce the final human-readable response after specialist agents
    have gathered their evidence.
    """

    def __init__(self, mcp_client: MCPPlanningClient) -> None:
        super().__init__(
            name="ExplanationAgent",
            instructions=_INSTRUCTIONS,
            mcp_client=mcp_client,
            tools=_make_tools(mcp_client),
        )
