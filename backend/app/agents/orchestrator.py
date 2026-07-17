"""Material Planning Orchestrator — routes user intent to the right MARA agent(s).

Architecture:
    POST /api/v1/planning/copilot
           ↓
    MaterialPlanningOrchestrator.run_chat()
           ↓
    Triage Agent (LLM) → selects specialist agent(s)
           ↓
    InventoryAgent | ProductionAgent | SupplierAgent | ReplenishmentAgent
           ↓  (all via MCPPlanningClient → MCP Server → Planning Services)
    ExplanationAgent → final grounded narrative
           ↓
    AgentLog written to database
           ↓
    {session_id, response, agent, evidence, tool_calls}

LLM role:
    ✅ Intent classification (which agent to call)
    ✅ Natural language explanation of tool results
    ❌ Never computes inventory numbers, risk scores, or recommendations
"""

import json
import logging
import traceback
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.inventory_agent import InventoryAgent
from app.agents.production_agent import ProductionAgent
from app.agents.supplier_agent import SupplierAgent
from app.agents.replenishment_agent import ReplenishmentAgent
from app.agents.explanation_agent import ExplanationAgent
from app.core.config import settings
from app.mcp.client import MCPPlanningClient
from app.models.agent_log import AgentLog

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Triage instructions — the orchestrator's own system prompt
# ---------------------------------------------------------------------------
_TRIAGE_INSTRUCTIONS = """
You are the Material Planning Orchestrator for MARA (Material Availability &
Replenishment Agent). Your job is to analyse the user's question and delegate
it to the most appropriate specialist agent.

Available specialist agents and their domains:
  - InventoryAgent:     stock levels, safety stock, usable inventory, material health
  - ProductionAgent:    production orders at risk, BOM explosions, shortage timelines
  - SupplierAgent:      late POs, PO coverage gaps, supplier risk scores
  - ReplenishmentAgent: replenishment recommendations, transfers, dashboard KPIs

Routing rules:
  - If the question mentions "stock", "inventory", "on-hand", "usable", "safety stock"
    → route to InventoryAgent
  - If the question mentions "production order", "BOM", "shortage", "projection",
    "timeline", "when will", "days of coverage"
    → route to ProductionAgent
  - If the question mentions "PO", "purchase order", "supplier", "late delivery",
    "risk score", "reliability"
    → route to SupplierAgent
  - If the question mentions "recommend", "replenish", "transfer", "expedite",
    "reorder", "dashboard", "KPI", "summary"
    → route to ReplenishmentAgent
  - If the question requires combining multiple data sources
    → route to multiple agents, then ExplanationAgent for synthesis

Always call the delegated agent's run() method with the original user message.
Return only the agent's response — do not add your own commentary.
"""


class MaterialPlanningOrchestrator:
    """Orchestrates MARA agents to answer manufacturing planning questions.

    Usage (called from planning_api.py endpoint):
        orchestrator = MaterialPlanningOrchestrator(db)
        result = await orchestrator.run_chat(session_id, user_message)

    The orchestrator:
        1. Creates a shared MCPPlanningClient (all agents share one client).
        2. Uses the LLM to classify intent and select the right agent.
        3. Delegates to the selected agent(s).
        4. Optionally calls ExplanationAgent to refine/synthesise the answer.
        5. Writes an AgentLog entry to the database.
        6. Returns a structured response dict.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        # Shared MCP client — all agents communicate through this
        self._mcp = MCPPlanningClient(
            base_url=settings.MCP_SERVER_URL,
            timeout=settings.MCP_SERVER_TIMEOUT,
        )
        # Specialist agents (lazy — LLM client created on first run() call)
        self._inventory = InventoryAgent(self._mcp)
        self._production = ProductionAgent(self._mcp)
        self._supplier = SupplierAgent(self._mcp)
        self._replenishment = ReplenishmentAgent(self._mcp)
        self._explanation = ExplanationAgent(self._mcp)

        # Triage agent — created lazily so app starts without OPENAI_API_KEY
        self._triage: Any = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_chat(self, session_id: str, message: str) -> dict:
        """Process a user planning question end-to-end.

        Args:
            session_id: Caller-provided session identifier for logging.
            message:    Natural language question from the planning user.

        Returns:
            dict with keys:
                session_id  — echoed back
                response    — natural language answer
                agent       — name of the primary agent that handled the query
                evidence    — structured data returned by tool calls
                tool_calls  — list of MCP tool names that were invoked
        """
        import time
        start_time = time.time()
        logger.info("[COPILOT REQUEST] Session ID: %s, Message: '%s'", session_id, message)
        
        agent_name = "MaterialPlanningOrchestrator"
        evidence: dict[str, Any] = {}
        tool_calls: list[str] = []
        response = ""
        tokens_used = 0

        try:
            # Step 1: classify intent via keyword routing
            # (fast deterministic routing — avoids an extra LLM call for simple cases)
            msg_lower = message.lower()
            selected_agent, agent_name, selected_tools = self._route(msg_lower)

            tool_calls = selected_tools
            logger.info("[ROUTING] Query routed to specialist agent: %s, associated tools: %s", agent_name, tool_calls)

            # Step 2: delegate to the selected specialist agent
            raw_response = await selected_agent.run(message)
            response = raw_response.text
            if raw_response.usage_details:
                tokens_used += raw_response.usage_details.get("total_token_count") or 0

            # Step 3: collect evidence from MCP for structured return
            evidence = await self._collect_evidence(msg_lower, tool_calls)

            # Step 4: if multiple domains detected, synthesise with ExplanationAgent
            if self._needs_synthesis(msg_lower):
                logger.info("[SYNTHESIS] Multi-domain query detected. Synthesis initiated via ExplanationAgent.")
                synthesis_prompt = (
                    f"Synthesise the following specialist agent response into a "
                    f"single clear answer. Original question: '{message}'\n\n"
                    f"Agent response: {response}"
                )
                synthesis_response = await self._explanation.run(synthesis_prompt)
                response = synthesis_response.text
                if synthesis_response.usage_details:
                    tokens_used += synthesis_response.usage_details.get("total_token_count") or 0
                agent_name = "ExplanationAgent (synthesised)"

            duration = time.time() - start_time
            logger.info("[COPILOT SUCCESS] Session ID: %s, Agent: %s, Tokens used: %s, Duration: %.2fs", session_id, agent_name, tokens_used, duration)

        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                "[COPILOT ERROR] Orchestrator error session=%s: %s\n%s",
                session_id, exc, traceback.format_exc(),
            )
            response = (
                "I encountered an error while processing your request. "
                f"Details: {str(exc)}"
            )

        finally:
            # Step 5: always write an AgentLog entry
            await self._write_log(session_id, agent_name, message, response, evidence, tokens_used)

        return {
            "session_id": session_id,
            "response": response,
            "agent": agent_name,
            "evidence": evidence,
            "tool_calls": tool_calls,
        }

    # ------------------------------------------------------------------
    # Internal routing helpers
    # ------------------------------------------------------------------

    def _route(self, msg_lower: str) -> tuple:
        """Keyword-based intent routing.

        Returns (agent_instance, agent_name, tool_names_list).
        Fast and deterministic — avoids burning an extra LLM token for routing.
        Falls back to ExplanationAgent for unrecognised queries.
        """
        # Production / shortage / projection keywords
        if any(
            kw in msg_lower
            for kw in (
                "production order", "bom", "projection", "timeline",
                "shortage", "days of coverage", "when will", "blocked",
                "impacted", "component", "assembly",
            )
        ):
            return self._production, "ProductionAgent", [
                "analyze_production_impact", "calculate_projection"
            ]

        # Supplier / PO / risk keywords
        if any(
            kw in msg_lower
            for kw in (
                "purchase order", " po ", "supplier", "late", "delivery",
                "risk score", "reliability", "po coverage", "overdue",
            )
        ):
            return self._supplier, "SupplierAgent", [
                "analyze_po_coverage", "get_material_risk"
            ]

        # Replenishment / recommendation / transfer keywords
        if any(
            kw in msg_lower
            for kw in (
                "recommend", "replenish", "transfer", "expedite",
                "reorder", "dashboard", "kpi", "summary", "suggest",
            )
        ):
            return self._replenishment, "ReplenishmentAgent", [
                "recommend_replenishment", "get_dashboard_kpis",
                "compare_plants", "explain_recommendation",
            ]

        # Inventory / stock / safety stock keywords
        if any(
            kw in msg_lower
            for kw in (
                "stock", "inventory", "on-hand", "on hand", "usable",
                "safety stock", "buffer", "reorder point", "health",
                "available", "material", "plant",
            )
        ):
            return self._inventory, "InventoryAgent", [
                "get_inventory_health", "get_material_health", "compare_plants"
            ]

        # Default: explanation agent with full tool access
        return self._explanation, "ExplanationAgent", [
            "get_inventory_health", "get_material_risk", "recommend_replenishment"
        ]

    def _needs_synthesis(self, msg_lower: str) -> bool:
        """Return True if the question spans multiple domains."""
        domain_hits = sum([
            any(kw in msg_lower for kw in ("stock", "inventory", "health")),
            any(kw in msg_lower for kw in ("production", "order", "bom")),
            any(kw in msg_lower for kw in ("supplier", "po ", "late")),
            any(kw in msg_lower for kw in ("recommend", "transfer", "replenish")),
        ])
        return domain_hits >= 2

    async def _collect_evidence(
        self, msg_lower: str, tool_calls: list[str]
    ) -> dict[str, Any]:
        """Collect a lightweight evidence snapshot for the response envelope.

        Fetches dashboard KPIs as a baseline for all responses so the
        frontend always has current numbers alongside the narrative.
        """
        evidence: dict[str, Any] = {}
        try:
            kpi_result = await self._mcp.call_tool("get_dashboard_kpis")
            if isinstance(kpi_result, dict) and kpi_result.get("success"):
                evidence["dashboard_kpis"] = kpi_result.get("data", {})
        except Exception as exc:
            logger.warning("Evidence collection failed: %s", exc)
        evidence["tool_calls_made"] = tool_calls
        return evidence

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    async def _write_log(
        self,
        session_id: str,
        agent_name: str,
        message: str,
        response: str,
        evidence: dict,
        tokens_used: int = 0,
    ) -> None:
        """Persist an AgentLog entry to the database."""
        try:
            log = AgentLog(
                agent_name=agent_name,
                session_id=session_id,
                action="planning_copilot",
                input_data=json.dumps({"user_message": message}),
                output_data=json.dumps({
                    "response": response[:2000],  # truncate large responses
                    "evidence": evidence,
                }),
                tokens_used=tokens_used,
            )
            self.db.add(log)
            await self.db.flush()
        except Exception as exc:
            # Log failures must never crash the main request
            logger.error("Failed to write AgentLog: %s", exc)
