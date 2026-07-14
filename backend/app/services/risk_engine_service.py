"""Risk Engine Service."""

from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import joinedload
from app.models.material import Material, MaterialCriticality
from app.models.plant import Plant
from app.models.inventory import Inventory
from app.models.material_risk import MaterialRisk
from app.models.supplier_performance import SupplierPerformance
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.services.projection_service import ProjectionService
from app.services.po_analysis_service import POAnalysisService


class RiskEngineService:
    """
    Computes deterministic risk scores (0-100) for materials across plants.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_and_save_risks(self) -> list[dict]:
        """
        Evaluate and compute the risk score for all material-plant combinations.
        Optimized with bulk loading to avoid N+1 query loops.
        """
        # Clear existing risks
        await self.db.execute(delete(MaterialRisk))
        await self.db.commit()

        # Eagerly load all database tables
        from app.services.bulk_planning_loader import BulkPlanningData
        bulk_data = BulkPlanningData(self.db)
        await bulk_data.load_all()

        po_service = POAnalysisService(self.db)
        po_coverage = await po_service.analyze_po_coverage()
        po_coverage_dict = {(p["material_id"], p["plant_id"]): p for p in po_coverage}

        # Bulk load supplier performance records
        perf_stmt = select(SupplierPerformance)
        perf_res = await self.db.execute(perf_stmt)
        perfs = perf_res.scalars().all()
        perf_map = {p.supplier_id: p for p in perfs}

        # Bulk load PO items to link material_id to supplier_id
        po_supplier_stmt = select(PurchaseOrderItem.material_id, PurchaseOrder.supplier_id).join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
        po_supplier_res = await self.db.execute(po_supplier_stmt)
        po_suppliers = po_supplier_res.all()
        material_supplier_map = {mat_id: sup_id for mat_id, sup_id in po_suppliers}

        risks = []
        for inv in bulk_data.inventories:
            material = inv.material
            plant = inv.plant
            if not material or not plant:
                continue

            # 1. Run projection in-memory (extremely fast)
            proj = bulk_data.calculate_projection_in_memory(material.id, plant.id)
            days_cov = proj["days_of_coverage"]
            shortage_qty = proj["shortage_quantity"]
            first_shortage_date = proj["first_shortage_date"]
            recovery_date = None  # Simplified/calculated on demand

            # 2. Risk factors (raw scores)
            # A. Urgency: higher risk if shortage occurs sooner
            urgency_score = 0.0
            if first_shortage_date is not None:
                # 0 days of coverage = 40 points, 30 days = 0 points
                urgency_score = max(0.0, (30.0 - days_cov) * 1.33)

            # B. Material Criticality
            criticality_score = 0.0
            if material.criticality == MaterialCriticality.HIGH:
                criticality_score = 30.0
            elif material.criticality == MaterialCriticality.MEDIUM:
                criticality_score = 15.0
            else:
                criticality_score = 5.0

            # C. Production Impact (from PO coverage / shortages)
            prod_impact_score = 0.0
            cov_data = po_coverage_dict.get((material.id, plant.id))
            impacted_orders_count = len(cov_data["impacted_orders"]) if cov_data else 0
            prod_impact_score = min(30.0, impacted_orders_count * 10.0)

            # D. Supplier Delay (Lead time variance from performance record)
            supplier_delay_score = 0.0
            sup_id = material_supplier_map.get(material.id)
            if sup_id:
                perf = perf_map.get(sup_id)
                if perf:
                    supplier_delay_score = min(20.0, perf.lead_time_variance * 4.0)

            # E. Safety Stock Violation
            safety_violation_score = 0.0
            usable = inv.usable_inventory
            if usable <= 0:
                safety_violation_score = 30.0
            elif usable <= inv.buffer_stock:
                safety_violation_score = 20.0
            elif usable <= inv.safety_stock:
                safety_violation_score = 10.0

            # F. Late POs count
            late_po_score = 0.0
            if cov_data:
                late_pos_count = sum(1 for po in cov_data["open_pos"] if po["is_late"])
                late_po_score = min(20.0, late_pos_count * 10.0)

            # 3. Sum up and normalize to 0-100
            total_raw = urgency_score + criticality_score + prod_impact_score + supplier_delay_score + safety_violation_score + late_po_score
            normalized_score = min(100.0, total_raw)

            # Generate reasoning explanation
            reasons = []
            if first_shortage_date:
                reasons.append(f"Shortage expected on {first_shortage_date.isoformat()} (Days of coverage: {days_cov}d)")
            if safety_violation_score >= 20.0:
                reasons.append("Safety stock completely violated")
            if prod_impact_score > 0:
                reasons.append(f"Production Impact: {impacted_orders_count} orders at risk")
            if late_po_score > 0:
                reasons.append("Incoming shipments are late")

            reason_str = "; ".join(reasons) if reasons else "Inventory level is healthy"

            db_risk = MaterialRisk(
                material_id=material.id,
                plant_id=plant.id,
                risk_score=normalized_score,
                urgency=urgency_score,
                material_criticality=criticality_score,
                production_impact=prod_impact_score,
                supplier_delay=supplier_delay_score,
                safety_stock_violation=safety_violation_score,
                late_po=late_po_score,
                reason=reason_str,
                first_shortage_date=first_shortage_date,
                shortage_quantity=shortage_qty,
                recovery_date=recovery_date,
                days_of_coverage=days_cov
            )
            self.db.add(db_risk)
            risks.append({
                "material_id": material.id,
                "material_code": material.material_code,
                "material_name": material.name,
                "plant_id": plant.id,
                "plant_name": plant.name,
                "risk_score": normalized_score,
                "reason": reason_str,
                "days_of_coverage": days_cov,
                "first_shortage_date": first_shortage_date.isoformat() if first_shortage_date else None
            })

        await self.db.flush()
        return risks
