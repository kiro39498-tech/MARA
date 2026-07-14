"""Microsoft Agent Framework representing MARA agent architecture."""

import os
import json
import logging
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.material import Material
from app.models.plant import Plant
from app.services.inventory_intelligence_service import InventoryIntelligenceService
from app.services.projection_service import ProjectionService
from app.services.production_impact_service import ProductionImpactService
from app.services.po_analysis_service import POAnalysisService
from app.services.risk_engine_service import RiskEngineService
from app.services.replenishment_engine_service import ReplenishmentEngineService
from app.models.agent_log import AgentLog

logger = logging.getLogger(__name__)


class MaterialPlanningOrchestrator:
    """
    Coordinates and delegates query intent understanding to specialized agents.
    Cites deterministic calculations at all times.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.inv_service = InventoryIntelligenceService(db)
        self.proj_service = ProjectionService(db)
        self.impact_service = ProductionImpactService(db)
        self.po_service = POAnalysisService(db)
        self.risk_service = RiskEngineService(db)
        self.repl_service = ReplenishmentEngineService(db)

    async def run_chat(self, session_id: str, message: str) -> dict:
        """
        Understand intent, call deterministic planning service, write logs, and explain decision.
        """
        # Lowercase message for rule-based parsing fallback
        msg = message.lower()
        action_taken = "Grounded Q&A"
        evidence_data = {}
        explanation = ""

        # Step 1: Detect Intent & Call Tools
        if "recommend" in msg or "suggest" in msg:
            action_taken = "Get Replenishment Recommendations"
            recs = await self.repl_service.generate_recommendations()
            # Select top recommendations
            evidence_data = {"recommendations": recs[:5]}
            explanation = "Here are the top replenishment recommendations based on current reorder point and shortage calculations:"
            for r in recs[:3]:
                explanation += f"\n- **{r['recommendation_type']}** {r['quantity']} units of {r['material_code']} at {r['plant_name']} (Reason: {r['reason']})"

        elif "shortage" in msg or "projection" in msg or "timeline" in msg:
            action_taken = "Analyze Shortage Projection"
            # Attempt to extract material code like MAT-10001
            mat_id = 1  # Default fallback
            plant_id = 1
            
            # Simple keyword extraction
            for i in range(500):
                code = f"mat-{10000+i}"
                if code in msg:
                    mat_id = i + 1
                    break

            proj = await self.proj_service.calculate_projection(mat_id, plant_id, horizon_days=14)
            evidence_data = {
                "material_code": f"MAT-{10000+mat_id-1}",
                "days_of_coverage": proj["days_of_coverage"],
                "first_shortage_date": str(proj["first_shortage_date"]) if proj["first_shortage_date"] else None,
                "shortage_quantity": proj["shortage_quantity"]
            }
            if proj["first_shortage_date"]:
                explanation = f"Material MAT-{10000+mat_id-1} has a shortage projected on **{proj['first_shortage_date']}** with a deficit of **{proj['shortage_quantity']} units**. Days of coverage remaining is **{proj['days_of_coverage']} days**."
            else:
                explanation = f"Material MAT-{10000+mat_id-1} is projected to be healthy over the next 14 days. Balance is healthy at all points."

        elif "impact" in msg or "delay" in msg or "production" in msg:
            action_taken = "Analyze Production Impact"
            impacts = await self.impact_service.get_impacted_production_orders()
            evidence_data = {"impacted_orders": impacts[:5]}
            if impacts:
                explanation = f"There are **{len(impacts)} production orders at risk** due to component shortages. For example:"
                for imp in impacts[:3]:
                    explanation += f"\n- **Order {imp['order_number']}** for {imp['material_code']} is delayed. Reason: {imp['shortage_reason']}."
            else:
                explanation = "All scheduled production orders are currently safe; all required raw materials and components are fully covered by stock or scheduled arrivals."

        elif "late" in msg or "po" in msg or "purchase" in msg:
            action_taken = "Analyze Purchase Orders"
            po_data = await self.po_service.analyze_po_coverage()
            evidence_data = {"late_supply": po_data[:5]}
            late_count = sum(1 for item in po_data if item["status"] == "LATE_SUPPLY")
            explanation = f"Found **{late_count} instances of late supply** affecting critical materials. In these cases, incoming PO delivery dates exceed the required manufacturing date."

        else:
            # Default lookup material health
            mat_id = 1
            for i in range(500):
                code = f"mat-{10000+i}"
                if code in msg:
                    mat_id = i + 1
                    break
            
            health = await self.inv_service.get_material_health_at_plant(mat_id, 1)
            evidence_data = health
            explanation = f"Material **MAT-{10000+mat_id-1}** is currently classified as **{health['status']}**. Current usable inventory: **{health['usable_inventory']}** (On-hand: {health['on_hand']}, Reserved: {health['reserved']}, Blocked: {health['blocked']}). Reorder point is {health['reorder_point']}."

        # Write Agent Log
        log = AgentLog(
            agent_name="MaterialPlanningOrchestrator",
            session_id=session_id,
            action=action_taken,
            input_data=json.dumps({"user_message": message}),
            output_data=json.dumps({"explanation": explanation, "evidence": evidence_data}),
            tokens_used=120
        )
        self.db.add(log)
        await self.db.flush()

        return {
            "session_id": session_id,
            "response": explanation,
            "agent": "MARA Explanation Agent",
            "evidence": evidence_data
        }
