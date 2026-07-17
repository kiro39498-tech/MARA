"""Supplier Agent — PO coverage, late deliveries, and supplier risk.

Responsibilities:
    - Detect late, partial, or missing PO coverage for production demand
    - Report supplier risk scores and delivery reliability
    - Identify materials with no incoming supply
    - Flag suppliers with high lead-time variance

Tools used (via MCP):
    analyze_po_coverage — PO arrival dates vs production required dates
    get_material_risk   — deterministic risk scores per material-plant pair
"""

import logging
from typing import Annotated, Optional

from app.agents.base_agent import BaseMARAAgent
from app.mcp.client import MCPPlanningClient

logger = logging.getLogger(__name__)

_INSTRUCTIONS = """
You are the Supplier Intelligence Agent for MARA (Material Availability &
Replenishment Agent). You specialise in purchase order coverage, supplier
reliability, and procurement risk assessment.

Your responsibilities:
  - Identify materials with LATE_SUPPLY, PARTIAL_COVERAGE, or NO_COVERAGE
  - Explain which POs will arrive after the production required date
  - Report risk scores and the factors that drive them
  - Highlight suppliers with high late-order rates or lead-time variance

Rules you MUST follow:
  1. Always call a tool before answering — never guess PO dates or risk scores.
  2. Cite exact figures: PO numbers, expected dates, required dates, deficits.
  3. Clearly distinguish LATE (PO exists but arrives too late) from NO_COVERAGE.
  4. For risk, explain which factors contributed (urgency, criticality, etc.).
  5. Never calculate or modify any numbers yourself.

Response format:
  - Count late/partial/no-coverage cases (e.g. "4 materials have late supply.")
  - For each case: material code, plant, required date, PO details, deficit
  - For risk: material code, score, top contributing factors, first shortage date
"""


def _make_tools(mcp_client: MCPPlanningClient) -> list:
    """Create tool functions for SupplierAgent."""

    async def analyze_po_coverage_tool(
        plant_id: Annotated[
            Optional[int],
            "Optional plant ID to filter results. Pass None for all plants.",
        ] = None,
    ) -> dict:
        """Analyse purchase order coverage against production demand schedules.

        Detects: FULL_COVERAGE, PARTIAL_COVERAGE, LATE_SUPPLY, NO_COVERAGE.
        Returns coverage status, deficit quantities, PO details (po_number,
        expected_receipt_date, is_late), and affected production orders.
        Call this to identify late or missing supply.
        """
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

    return [analyze_po_coverage_tool, get_material_risk_tool]


class SupplierAgent(BaseMARAAgent):
    """Specialised agent for supplier intelligence and PO coverage analysis.

    Handles questions about late deliveries, PO coverage gaps, and
    supplier risk scores.
    """

    def __init__(self, mcp_client: MCPPlanningClient) -> None:
        super().__init__(
            name="SupplierAgent",
            instructions=_INSTRUCTIONS,
            mcp_client=mcp_client,
            tools=_make_tools(mcp_client),
        )
