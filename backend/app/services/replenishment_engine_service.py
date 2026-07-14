"""Replenishment Recommendation Engine Service."""

from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import joinedload
from app.models.inventory import Inventory
from app.models.material import Material
from app.models.plant import Plant
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.replenishment_recommendation import ReplenishmentRecommendation
from app.services.projection_service import ProjectionService
from app.services.po_analysis_service import POAnalysisService


class ReplenishmentEngineService:
    """
    Evaluates safety stock violations, reorder points, and cross-plant excess stock to recommend supply actions.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_recommendations(self) -> list[dict]:
        """
        Runs the replenishment rule engine to generate evidence-backed recommendations.
        Optimized with bulk loading to avoid N+1 query loops.
        """
        # Clear existing suggestions
        await self.db.execute(delete(ReplenishmentRecommendation))
        await self.db.commit()

        # Eagerly load all database tables
        from app.services.bulk_planning_loader import BulkPlanningData
        bulk_data = BulkPlanningData(self.db)
        await bulk_data.load_all()

        po_service = POAnalysisService(self.db)
        po_coverage = await po_service.analyze_po_coverage()
        po_coverage_dict = {(p["material_id"], p["plant_id"]): p for p in po_coverage}

        recommendations = []

        for inv in bulk_data.inventories:
            material = inv.material
            plant = inv.plant
            if not material or not plant:
                continue

            # Run projection in-memory (extremely fast)
            proj = bulk_data.calculate_projection_in_memory(material.id, plant.id)
            first_shortage_date = proj["first_shortage_date"]
            shortage_qty = proj["shortage_quantity"]
            days_cov = proj["days_of_coverage"]

            usable = inv.usable_inventory

            # Rule 1: Expedite Existing PO
            # If shortage is expected, and we have open POs that are arriving LATE
            cov_data = po_coverage_dict.get((material.id, plant.id))
            late_pos = [po for po in cov_data["open_pos"] if po["is_late"]] if cov_data else []

            if first_shortage_date and late_pos:
                rec_qty = shortage_qty
                # Recommend expediting the earliest late PO
                earliest_po = late_pos[0]
                rec = ReplenishmentRecommendation(
                    material_id=material.id,
                    plant_id=plant.id,
                    recommendation_type="Expedite Existing PO",
                    quantity=rec_qty,
                    order_date=date.today(),
                    eta_date=earliest_po["expected_receipt_date"],
                    reason=f"Expedite PO {earliest_po['po_number']}: it arrives on {earliest_po['expected_receipt_date']}, but a shortage occurs earlier on {first_shortage_date}.",
                    evidence=f"Deficit of {shortage_qty} expected on {first_shortage_date}. PO {earliest_po['po_number']} contains {earliest_po['quantity']} units.",
                    confidence=0.90,
                    priority="CRITICAL",
                    status="NEW"
                )
                self.db.add(rec)
                continue

            # Rule 2: Plant Transfer (Cross-Plant Analysis)
            # If shortage exists, check if another plant has excess inventory
            if first_shortage_date:
                excess_plant = None
                excess_qty = 0
                for other_inv in bulk_data.inventories:
                    if other_inv.material_id == material.id and other_inv.plant_id != plant.id:
                        # Excess is anything above safety stock + buffer stock
                        safety_buffer = other_inv.safety_stock + other_inv.buffer_stock
                        available_excess = other_inv.usable_inventory - safety_buffer
                        if available_excess > shortage_qty:
                            excess_plant = other_inv.plant
                            excess_qty = available_excess
                            break

                if excess_plant:
                    rec = ReplenishmentRecommendation(
                        material_id=material.id,
                        plant_id=plant.id,
                        recommendation_type="Transfer Between Plants",
                        quantity=shortage_qty,
                        order_date=date.today(),
                        eta_date=date.today() + timedelta(days=2),  # assume 2 days transport
                        source_plant_id=excess_plant.id,
                        reason=f"Transfer {shortage_qty} units from plant {excess_plant.name} to plant {plant.name} to cover shortage on {first_shortage_date}.",
                        evidence=f"Plant {excess_plant.name} has {excess_qty} units of excess stock. Deficit at plant {plant.name} is {shortage_qty} units.",
                        confidence=0.95,
                        priority="HIGH",
                        status="NEW"
                    )
                    self.db.add(rec)
                    continue

            # Rule 3: Replenish (Purchase Reorder)
            # If projected balance falls below reorder point or there is a shortage, and no other plant has excess
            if first_shortage_date or usable <= inv.reorder_point:
                req_qty = max(shortage_qty, inv.reorder_point - usable + inv.safety_stock)
                if req_qty > 0:
                    # Recommend purchasing from main supplier
                    lead_time = material.lead_time or 7
                    rec = ReplenishmentRecommendation(
                        material_id=material.id,
                        plant_id=plant.id,
                        recommendation_type="Replenish",
                        quantity=req_qty,
                        order_date=date.today(),
                        eta_date=date.today() + timedelta(days=lead_time),
                        reason=f"Reorder suggested as stock is below reorder point ({usable} <= {inv.reorder_point}) or shortage is imminent.",
                        evidence=f"Deficit: {req_qty} units. Lead time: {lead_time} days. Plant: {plant.name}.",
                        confidence=0.85,
                        priority="HIGH" if first_shortage_date else "MEDIUM",
                        status="NEW"
                    )
                    self.db.add(rec)
                    continue

            # Rule 4: Restore Safety Stock
            # If stock is fine for daily demand but below safety level
            if usable <= inv.safety_stock and usable > inv.reorder_point:
                req_qty = inv.safety_stock - usable
                if req_qty > 0:
                    lead_time = material.lead_time or 7
                    rec = ReplenishmentRecommendation(
                        material_id=material.id,
                        plant_id=plant.id,
                        recommendation_type="Restore Safety Stock",
                        quantity=req_qty,
                        order_date=date.today(),
                        eta_date=date.today() + timedelta(days=lead_time),
                        reason=f"Restock safety levels. Current usable inventory of {usable} is below safety stock setting of {inv.safety_stock}.",
                        evidence=f"Deficit from safety: {req_qty} units. Reorder point: {inv.reorder_point}.",
                        confidence=0.75,
                        priority="LOW",
                        status="NEW"
                    )
                    self.db.add(rec)

        await self.db.flush()

        # Query all generated and return
        stmt = select(ReplenishmentRecommendation).options(
            joinedload(ReplenishmentRecommendation.material),
            joinedload(ReplenishmentRecommendation.plant),
            joinedload(ReplenishmentRecommendation.source_plant)
        )
        res = await self.db.execute(stmt)
        recs = res.scalars().all()

        results = []
        for r in recs:
            results.append({
                "id": r.id,
                "material_id": r.material_id,
                "material_code": r.material.material_code if r.material else "N/A",
                "material_name": r.material.name if r.material else "N/A",
                "plant_id": r.plant_id,
                "plant_name": r.plant.name if r.plant else "N/A",
                "recommendation_type": r.recommendation_type,
                "quantity": r.quantity,
                "order_date": r.order_date.isoformat() if isinstance(r.order_date, date) else r.order_date,
                "eta_date": r.eta_date.isoformat() if isinstance(r.eta_date, date) else r.eta_date,
                "source_plant_id": r.source_plant_id,
                "source_plant_name": r.source_plant.name if r.source_plant else None,
                "reason": r.reason,
                "evidence": r.evidence,
                "confidence": r.confidence,
                "priority": r.priority,
                "status": r.status
            })

        return results
