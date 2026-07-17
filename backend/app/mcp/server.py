"""MARA MCP Planning Server.

This is the ONLY file in the agent layer that imports Planning Services.
Every planning capability is exposed here as an MCP tool decorated with @mcp.tool().

Architecture rules enforced here:
    ✅ This file routes requests to Planning Services — no business logic.
    ✅ Agents call this server through MCPPlanningClient — never directly.
    ✅ Each tool opens its own DB session and closes it after use.
    ❌ No calculations, scoring, or rule evaluation in this file.

Transport: streamable-http (JSON-RPC 2.0 over HTTP)
Default port: 8001 (configurable via MCP_SERVER_PORT)
"""

import logging
from typing import Annotated, Optional

from mcp.server.fastmcp import FastMCP

from app.core.database import AsyncSessionLocal
from app.services.inventory_intelligence_service import InventoryIntelligenceService
from app.services.projection_service import ProjectionService
from app.services.production_impact_service import ProductionImpactService
from app.services.po_analysis_service import POAnalysisService
from app.services.risk_engine_service import RiskEngineService
from app.services.replenishment_engine_service import ReplenishmentEngineService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="MARA Planning Server",
    instructions=(
        "This MCP server exposes deterministic manufacturing planning tools. "
        "All inventory calculations, projections, risk scores, and replenishment "
        "recommendations are computed by Python planning services. "
        "The LLM must NEVER compute numbers — it only explains results."
    ),
)


# ---------------------------------------------------------------------------
# Helper: get a fresh DB session per tool call
# ---------------------------------------------------------------------------
async def _get_db():
    """Open and return a new async DB session (caller must close it)."""
    return AsyncSessionLocal()


# ===========================================================================
# TOOL 1 — Inventory Health (all materials × all plants)
# ===========================================================================
@mcp.tool()
async def get_inventory_health(
    material_code: Annotated[Optional[str], "Optional material code to filter results by (e.g., MAT-1001)"] = None,
    plant_name: Annotated[Optional[str], "Optional plant name to filter results by (e.g., Plant A)"] = None,
) -> dict:
    """Get inventory health status across materials and plants.

    Returns a list of records with fields:
        material_id, material_code, material_name,
        plant_id, plant_name,
        on_hand, reserved, blocked, quality_hold, in_transit,
        safety_stock, buffer_stock, reorder_point,
        usable_inventory, status (HEALTHY | AT_RISK | CRITICAL | SHORTAGE)

    Use this tool to answer questions like:
        - How many materials are at risk?
        - Which materials are in shortage?
        - Show me the overall inventory health summary.
    """
    db = await _get_db()
    try:
        service = InventoryIntelligenceService(db)
        result = await service.get_all_inventory_health()
        await db.commit()

        if material_code:
            mat_lower = material_code.lower().strip()
            result = [r for r in result if mat_lower in r.get("material_code", "").lower()]
        if plant_name:
            plt_lower = plant_name.lower().strip()
            result = [r for r in result if plt_lower in r.get("plant_name", "").lower()]

        return {"success": True, "data": result, "count": len(result)}
    except Exception as exc:
        await db.rollback()
        logger.error("get_inventory_health failed: %s", exc)
        return {"success": False, "error": str(exc), "data": []}
    finally:
        await db.close()


# ===========================================================================
# TOOL 2 — Material Health at a specific plant
# ===========================================================================
@mcp.tool()
async def get_material_health(
    material_id: Annotated[int, "The integer ID of the material to check"],
    plant_id: Annotated[int, "The integer ID of the plant to check"],
) -> dict:
    """Get inventory health for a specific material at a specific plant.

    Returns:
        on_hand, reserved, blocked, quality_hold, in_transit,
        safety_stock, buffer_stock, reorder_point,
        usable_inventory, status (HEALTHY | AT_RISK | CRITICAL | SHORTAGE)

    Use this tool to answer questions like:
        - What is the current stock of RM102 at Plant A?
        - Is material 5 at plant 2 below safety stock?
        - Why is RM102 classified as critical?
    """
    db = await _get_db()
    try:
        service = InventoryIntelligenceService(db)
        result = await service.get_material_health_at_plant(material_id, plant_id)
        await db.commit()
        return {"success": True, "data": result}
    except Exception as exc:
        await db.rollback()
        logger.error(
            "get_material_health failed material_id=%s plant_id=%s: %s",
            material_id, plant_id, exc,
        )
        return {"success": False, "error": str(exc), "data": {}}
    finally:
        await db.close()


# ===========================================================================
# TOOL 3 — Time-phased projection (calculates + persists)
# ===========================================================================
@mcp.tool()
async def calculate_projection(
    material_id: Annotated[int, "The integer ID of the material"],
    plant_id: Annotated[int, "The integer ID of the plant"],
    horizon_days: Annotated[int, "Number of days to project forward (7–90)"] = 30,
) -> dict:
    """Calculate and return a time-phased material availability projection.

    Uses the formula: Projected Balance = Previous Balance + Incoming Supply − Production Demand

    Returns:
        initial_balance, horizon_days,
        first_shortage_date (null if no shortage),
        shortage_quantity, days_of_coverage, recovery_date,
        timeline: list of {date, projected_balance, incoming_supply, production_demand, shortage_flag}

    Use this tool to answer questions like:
        - Show me the shortage timeline for RM102.
        - When will material 3 run out at plant 1?
        - How many days of coverage does RM102 have?
    """
    db = await _get_db()
    try:
        service = ProjectionService(db)
        result = await service.calculate_projection(material_id, plant_id, horizon_days)
        await db.commit()
        # Convert date objects to ISO strings for JSON serialisation
        if result.get("first_shortage_date"):
            result["first_shortage_date"] = str(result["first_shortage_date"])
        if result.get("recovery_date"):
            result["recovery_date"] = str(result["recovery_date"])
        for day in result.get("timeline", []):
            if "date" in day:
                day["date"] = str(day["date"])
        return {"success": True, "data": result}
    except Exception as exc:
        await db.rollback()
        logger.error(
            "calculate_projection failed material_id=%s plant_id=%s: %s",
            material_id, plant_id, exc,
        )
        return {"success": False, "error": str(exc), "data": {}}
    finally:
        await db.close()


# ===========================================================================
# TOOL 4 — Analyse production impact (which orders are blocked by shortages)
# ===========================================================================
@mcp.tool()
async def analyze_production_impact(
    plant_id: Annotated[
        Optional[int],
        "Optional plant ID to filter results. Omit for all plants.",
    ] = None,
) -> dict:
    """Identify production orders that are at risk due to component shortages.

    Performs BOM explosion for every active production order and checks whether
    all required components have sufficient stock.

    Returns a list of impacted orders, each with:
        order_id, order_number, material_code, material_name,
        plant_id, plant_name, quantity, required_date, priority, status,
        shortages: [{component_code, required, available, deficit}],
        shortage_reason

    Use this tool to answer questions like:
        - Which production orders are affected by shortages?
        - Is production order PO-2001 at risk?
        - What component is blocking production at Plant A?
    """
    db = await _get_db()
    try:
        service = ProductionImpactService(db)
        result = await service.get_impacted_production_orders(plant_id)
        await db.commit()
        # Serialise date fields
        for order in result:
            if order.get("required_date"):
                order["required_date"] = str(order["required_date"])
        return {"success": True, "data": result, "count": len(result)}
    except Exception as exc:
        await db.rollback()
        logger.error("analyze_production_impact failed: %s", exc)
        return {"success": False, "error": str(exc), "data": []}
    finally:
        await db.close()


# ===========================================================================
# TOOL 5 — PO coverage analysis (late / partial / no coverage)
# ===========================================================================
@mcp.tool()
async def analyze_po_coverage(
    plant_id: Annotated[
        Optional[int],
        "Optional plant ID to filter results. Omit for all plants.",
    ] = None,
) -> dict:
    """Analyse purchase order coverage against production demand.

    Detects: FULL_COVERAGE, PARTIAL_COVERAGE, LATE_SUPPLY, NO_COVERAGE.

    Returns a list of coverage records, each with:
        material_id, material_code, plant_id, plant_name,
        required_date, deficit, status,
        open_pos: [{po_number, expected_receipt_date, quantity, is_late}],
        coverage_quantity, late_quantity,
        impacted_orders: [order_number, ...]

    Use this tool to answer questions like:
        - Which materials have late supply?
        - Are there any POs that will arrive after the production start date?
        - What is the PO coverage status for RM102 at Plant A?
    """
    db = await _get_db()
    try:
        service = POAnalysisService(db)
        result = await service.analyze_po_coverage(plant_id)
        await db.commit()
        return {"success": True, "data": result, "count": len(result)}
    except Exception as exc:
        await db.rollback()
        logger.error("analyze_po_coverage failed: %s", exc)
        return {"success": False, "error": str(exc), "data": []}
    finally:
        await db.close()


# ===========================================================================
# TOOL 6 — Material risk assessment (calculate + persist)
# ===========================================================================
@mcp.tool()
async def get_material_risk(
    material_code: Annotated[Optional[str], "Optional material code to filter results by (e.g., MAT-1001)"] = None,
    plant_name: Annotated[Optional[str], "Optional plant name to filter results by (e.g., Plant A)"] = None,
) -> dict:
    """Calculate deterministic risk scores (0–100) for material-plant combinations.

    Risk score formula (configurable weights):
        0.30 × Urgency
      + 0.25 × Production Impact
      + 0.20 × Material Criticality
      + 0.15 × Supplier Reliability
      + 0.10 × Safety Stock Violation
    Normalised to 0–100.

    Returns a list of risk records, each with:
        material_id, material_code, material_name,
        plant_id, plant_name,
        risk_score, reason,
        days_of_coverage, first_shortage_date

    Use this tool to answer questions like:
        - Which materials have the highest risk score?
        - Why is RM102 considered high risk?
        - Which supplier has the highest delay risk?
    """
    db = await _get_db()
    try:
        service = RiskEngineService(db)
        result = await service.calculate_and_save_risks()
        await db.commit()
        # Serialise date fields
        for record in result:
            if record.get("first_shortage_date"):
                record["first_shortage_date"] = str(record["first_shortage_date"])

        if material_code:
            mat_lower = material_code.lower().strip()
            result = [r for r in result if mat_lower in r.get("material_code", "").lower()]
        if plant_name:
            plt_lower = plant_name.lower().strip()
            result = [r for r in result if plt_lower in r.get("plant_name", "").lower()]

        return {"success": True, "data": result, "count": len(result)}
    except Exception as exc:
        await db.rollback()
        logger.error("get_material_risk failed: %s", exc)
        return {"success": False, "error": str(exc), "data": []}
    finally:
        await db.close()


# ===========================================================================
# TOOL 7 — Replenishment recommendations (calculate + persist)
# ===========================================================================
@mcp.tool()
async def recommend_replenishment(
    material_code: Annotated[Optional[str], "Optional material code to filter results by (e.g., MAT-1001)"] = None,
    plant_name: Annotated[Optional[str], "Optional plant name to filter results by (e.g., Plant A)"] = None,
) -> dict:
    """Generate evidence-backed replenishment recommendations.

    Applies a priority-ordered rule engine:
        Rule 1 — Expedite Existing Late PO
        Rule 2 — Transfer Stock Between Plants
        Rule 3 — Create New Purchase Order (Replenish)
        Rule 4 — Restore Safety Stock Levels

    Returns a list of recommendations, each with:
        material_id, material_code, plant_id, plant_name,
        recommendation_type, quantity, order_date, eta_date,
        source_plant_name (for transfers),
        reason, evidence, confidence, priority, status

    Use this tool to answer questions like:
        - What replenishment actions are recommended?
        - Should we transfer stock from Plant B to Plant A?
        - What should be ordered to cover the July 18 shortage?
    """
    db = await _get_db()
    try:
        service = ReplenishmentEngineService(db)
        result = await service.generate_recommendations()
        await db.commit()
        # Serialise date fields
        for rec in result:
            for key in ("order_date", "eta_date"):
                if rec.get(key) and not isinstance(rec[key], str):
                    rec[key] = str(rec[key])

        if material_code:
            mat_lower = material_code.lower().strip()
            result = [r for r in result if mat_lower in r.get("material_code", "").lower()]
        if plant_name:
            plt_lower = plant_name.lower().strip()
            result = [r for r in result if plt_lower in r.get("plant_name", "").lower()]

        return {"success": True, "data": result, "count": len(result)}
    except Exception as exc:
        await db.rollback()
        logger.error("recommend_replenishment failed: %s", exc)
        return {"success": False, "error": str(exc), "data": []}
    finally:
        await db.close()


# ===========================================================================
# TOOL 8 — Cross-plant inventory comparison for a material
# ===========================================================================
@mcp.tool()
async def compare_plants(
    material_id: Annotated[int, "The integer ID of the material to compare across plants"],
) -> dict:
    """Compare inventory levels for a material across all plants.

    Returns a list of per-plant records, each with:
        plant_id, plant_name,
        on_hand, usable_inventory,
        safety_stock, buffer_stock, reorder_point,
        status,
        excess_available (usable - safety_stock - buffer_stock, if positive)

    Use this tool to answer questions like:
        - Can another plant fulfil demand for RM102?
        - Which plant has the most excess stock of material 3?
        - Is there a cross-plant transfer opportunity?
    """
    db = await _get_db()
    try:
        service = InventoryIntelligenceService(db)
        all_health = await service.get_all_inventory_health()
        await db.commit()
        # Filter to the requested material and annotate excess
        plant_data = []
        for record in all_health:
            if record["material_id"] == material_id:
                usable = record["usable_inventory"]
                safety = record["safety_stock"]
                buffer = record["buffer_stock"]
                excess = usable - safety - buffer
                plant_data.append({
                    **record,
                    "excess_available": max(0, excess),
                })
        return {"success": True, "data": plant_data, "count": len(plant_data)}
    except Exception as exc:
        await db.rollback()
        logger.error("compare_plants failed material_id=%s: %s", material_id, exc)
        return {"success": False, "error": str(exc), "data": []}
    finally:
        await db.close()


# ===========================================================================
# TOOL 9 — Dashboard KPIs
# ===========================================================================
@mcp.tool()
async def get_dashboard_kpis() -> dict:
    """Return high-level planning dashboard KPIs.

    Returns:
        total_materials, total_plants,
        healthy_materials, at_risk_materials, critical_materials, shortage_materials,
        active_production_orders, open_purchase_orders,
        impacted_production_orders, safety_stock_violations, critical_shortages

    Use this tool to answer questions like:
        - Give me the planning dashboard summary.
        - How many materials are in shortage right now?
        - How many production orders are at risk?
    """
    from sqlalchemy import select, func
    from app.models.material import Material
    from app.models.plant import Plant
    from app.models.production_order import ProductionOrder
    from app.models.purchase_order import PurchaseOrder

    db = await _get_db()
    try:
        # Counts from DB
        mat_count = (await db.execute(select(func.count(Material.id)))).scalar() or 0
        plt_count = (await db.execute(select(func.count(Plant.id)))).scalar() or 0
        active_prod = (
            await db.execute(
                select(func.count(ProductionOrder.id)).where(
                    ProductionOrder.status.in_(["PLANNED", "IN_PROGRESS"])
                )
            )
        ).scalar() or 0
        open_po = (
            await db.execute(
                select(func.count(PurchaseOrder.id)).where(
                    PurchaseOrder.status.in_(["DRAFT", "SENT", "PARTIALLY_RECEIVED"])
                )
            )
        ).scalar() or 0

        # Inventory health summary
        inv_service = InventoryIntelligenceService(db)
        all_health = await inv_service.get_all_inventory_health()

        status_counts: dict[str, int] = {"HEALTHY": 0, "AT_RISK": 0, "CRITICAL": 0, "SHORTAGE": 0}
        for h in all_health:
            status_counts[h["status"]] = status_counts.get(h["status"], 0) + 1

        safety_violations = sum(
            1 for h in all_health if h["status"] in ("AT_RISK", "CRITICAL", "SHORTAGE")
        )
        critical_shortages = sum(
            1 for h in all_health if h["status"] in ("CRITICAL", "SHORTAGE")
        )

        # Production impact
        impact_service = ProductionImpactService(db)
        impacted = await impact_service.get_impacted_production_orders()

        await db.commit()
        return {
            "success": True,
            "data": {
                "total_materials": mat_count,
                "total_plants": plt_count,
                "healthy_materials": status_counts.get("HEALTHY", 0),
                "at_risk_materials": status_counts.get("AT_RISK", 0),
                "critical_materials": status_counts.get("CRITICAL", 0),
                "shortage_materials": status_counts.get("SHORTAGE", 0),
                "active_production_orders": active_prod,
                "open_purchase_orders": open_po,
                "impacted_production_orders": len(impacted),
                "safety_stock_violations": safety_violations,
                "critical_shortages": critical_shortages,
            },
        }
    except Exception as exc:
        await db.rollback()
        logger.error("get_dashboard_kpis failed: %s", exc)
        return {"success": False, "error": str(exc), "data": {}}
    finally:
        await db.close()


# ===========================================================================
# TOOL 10 — Explain a recommendation by ID
# ===========================================================================
@mcp.tool()
async def explain_recommendation(
    recommendation_id: Annotated[int, "The integer ID of the replenishment recommendation to explain"],
) -> dict:
    """Retrieve the full evidence and explanation for a replenishment recommendation.

    Returns:
        recommendation_type, quantity, priority, confidence,
        reason, evidence, eta_date,
        material_code, plant_name, source_plant_name

    Use this tool to answer questions like:
        - Why is recommendation #5 marked as critical?
        - What is the evidence behind the Plant B → Plant A transfer suggestion?
        - Explain the reasoning for recommending a new PO for RM102.
    """
    from sqlalchemy import select
    from app.models.replenishment_recommendation import ReplenishmentRecommendation

    db = await _get_db()
    try:
        stmt = select(ReplenishmentRecommendation).where(
            ReplenishmentRecommendation.id == recommendation_id
        )
        result = await db.execute(stmt)
        rec = result.scalar_one_or_none()
        await db.commit()

        if not rec:
            return {
                "success": False,
                "error": f"Recommendation {recommendation_id} not found.",
                "data": {},
            }

        return {
            "success": True,
            "data": {
                "id": rec.id,
                "recommendation_type": rec.recommendation_type,
                "quantity": rec.quantity,
                "priority": rec.priority,
                "confidence": rec.confidence,
                "status": rec.status,
                "reason": rec.reason,
                "evidence": rec.evidence,
                "order_date": str(rec.order_date) if rec.order_date else None,
                "eta_date": str(rec.eta_date) if rec.eta_date else None,
                "material_code": rec.material.material_code if rec.material else None,
                "material_name": rec.material.name if rec.material else None,
                "plant_name": rec.plant.name if rec.plant else None,
                "source_plant_name": rec.source_plant.name if rec.source_plant else None,
            },
        }
    except Exception as exc:
        await db.rollback()
        logger.error(
            "explain_recommendation failed recommendation_id=%s: %s",
            recommendation_id, exc,
        )
        return {"success": False, "error": str(exc), "data": {}}
    finally:
        await db.close()
