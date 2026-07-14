"""Planning and Decision Support System endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import check_permission
from app.services.inventory_intelligence_service import InventoryIntelligenceService
from app.services.projection_service import ProjectionService
from app.services.production_impact_service import ProductionImpactService
from app.services.po_analysis_service import POAnalysisService
from app.services.risk_engine_service import RiskEngineService
from app.services.replenishment_engine_service import ReplenishmentEngineService
from app.services.agent_framework import MaterialPlanningOrchestrator
from app.models.material import Material
from app.models.plant import Plant
from app.models.inventory import Inventory
from app.models.production_order import ProductionOrder
from app.models.purchase_order import PurchaseOrder

router = APIRouter()


@router.get("/inventory-health")
async def get_inventory_health(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(check_permission("ai:forecast:view")),
):
    """Retrieve full inventory health across plants."""
    service = InventoryIntelligenceService(db)
    return await service.get_all_inventory_health()


@router.get("/projection")
async def get_projection(
    material_id: int = Query(..., ge=1),
    plant_id: int = Query(..., ge=1),
    horizon_days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(check_permission("ai:forecast:view")),
):
    """Retrieve time-phased projection for a material at a plant."""
    service = ProjectionService(db)
    return await service.calculate_projection(material_id, plant_id, horizon_days)


@router.get("/material-risk")
async def get_material_risk(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(check_permission("ai:forecast:view")),
):
    """Calculate and return material risks across plants."""
    service = RiskEngineService(db)
    return await service.calculate_and_save_risks()


@router.get("/production-impact")
async def get_production_impact(
    plant_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(check_permission("ai:forecast:view")),
):
    """Retrieve impacted production orders due to shortages."""
    service = ProductionImpactService(db)
    return await service.get_impacted_production_orders(plant_id)


@router.get("/po-analysis")
async def get_po_analysis(
    plant_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(check_permission("ai:forecast:view")),
):
    """Retrieve PO coverage analysis of shortages."""
    service = POAnalysisService(db)
    return await service.analyze_po_coverage(plant_id)


@router.get("/recommendations")
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(check_permission("ai:forecast:view")),
):
    """Calculate and return replenishment suggestions."""
    service = ReplenishmentEngineService(db)
    return await service.generate_recommendations()


@router.get("/dashboard-kpis")
async def get_dashboard_kpis(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(check_permission("ai:forecast:view")),
):
    """Calculate high-level planning dashboard KPIs."""
    # 1. Total materials count
    mat_count_stmt = select(func.count(Material.id))
    mat_count_res = await db.execute(mat_count_stmt)
    total_materials = mat_count_res.scalar() or 0

    # 2. Total plants count
    plt_count_stmt = select(func.count(Plant.id))
    plt_count_res = await db.execute(plt_count_stmt)
    total_plants = plt_count_res.scalar() or 0

    # 3. Active production orders
    po_count_stmt = select(func.count(ProductionOrder.id)).where(ProductionOrder.status.in_(["PLANNED", "IN_PROGRESS"]))
    po_count_res = await db.execute(po_count_stmt)
    active_prod_orders = po_count_res.scalar() or 0

    # 4. Open purchase orders
    pur_count_stmt = select(func.count(PurchaseOrder.id)).where(PurchaseOrder.status.in_(["DRAFT", "SENT", "PARTIALLY_RECEIVED"]))
    pur_count_res = await db.execute(pur_count_stmt)
    open_purchases = pur_count_res.scalar() or 0

    # 5. Shortage alert materials
    # We can run ProductionImpactService to find how many production orders are impacted
    impact_service = ProductionImpactService(db)
    impacted = await impact_service.get_impacted_production_orders()
    impacted_orders_count = len(impacted)

    # 6. Safety stock violations count
    inv_service = InventoryIntelligenceService(db)
    all_health = await inv_service.get_all_inventory_health()
    safety_violations = sum(1 for h in all_health if h["status"] in ["AT_RISK", "CRITICAL", "SHORTAGE"])
    critical_shortages = sum(1 for h in all_health if h["status"] in ["CRITICAL", "SHORTAGE"])

    return {
        "total_materials": total_materials,
        "total_plants": total_plants,
        "active_production_orders": active_prod_orders,
        "open_purchase_orders": open_purchases,
        "impacted_production_orders": impacted_orders_count,
        "safety_stock_violations": safety_violations,
        "critical_shortages": critical_shortages
    }


from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/copilot")
async def copilot_chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(check_permission("ai:forecast:view")),
):
    """Interact with the Grounded Planning Copilot agent."""
    orchestrator = MaterialPlanningOrchestrator(db)
    try:
        return await orchestrator.run_chat(payload.session_id, payload.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration error: {str(e)}"
        )
