"""PO Analysis Service."""

from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.production_order import ProductionOrder
from app.models.inventory import Inventory
from app.services.production_impact_service import ProductionImpactService


class POAnalysisService:
    """
    Evaluates Purchase Order coverage relative to production demand schedules.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_po_coverage(self, plant_id: int = None) -> list[dict]:
        """
        Analyze all open PO items and detect Late Supply, Partial Coverage, or No Coverage.
        Optimized with bulk loading to avoid N+1 query loops.
        """
        # Find all open production orders first (Demand)
        impact_service = ProductionImpactService(self.db)
        impacted_orders = await impact_service.get_impacted_production_orders(plant_id)

        # Build component demands
        needed_components = {}
        for io in impacted_orders:
            # Check shortages
            for sh in io.get("shortages", []):
                comp_id = sh["component_id"]
                plant_id_curr = io["plant_id"]
                key = (comp_id, plant_id_curr)
                if key not in needed_components:
                    needed_components[key] = {
                        "material_id": comp_id,
                        "material_code": sh["component_code"],
                        "material_name": sh["component_name"],
                        "plant_id": plant_id_curr,
                        "plant_name": io["plant_name"],
                        "required_date": io["required_date"],
                        "deficit": 0.0,
                        "impacted_orders": []
                    }
                needed_components[key]["deficit"] += sh["deficit"]
                # Keep earliest required date
                # Handle both date and string types for safety
                req_date = io["required_date"]
                if key in needed_components:
                    needed_components[key]["required_date"] = min(needed_components[key]["required_date"], req_date)
                else:
                    needed_components[key]["required_date"] = req_date
                needed_components[key]["impacted_orders"].append(io["order_number"])

        # Bulk query all open PO items
        stmt = (
            select(
                PurchaseOrderItem.material_id,
                PurchaseOrderItem.quantity,
                PurchaseOrderItem.received_quantity,
                PurchaseOrder.plant_id,
                PurchaseOrder.expected_receipt_date,
                PurchaseOrder.po_number,
                PurchaseOrder.id
            )
            .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
            .where(
                PurchaseOrder.status.in_(["DRAFT", "SENT", "PARTIALLY_RECEIVED"])
            )
            .order_by(PurchaseOrder.expected_receipt_date.asc())
        )
        res = await self.db.execute(stmt)
        all_po_items = res.all()

        # Group PO items by (material_id, plant_id)
        po_items_map = {}
        for mat_id, qty, rec_qty, pl_id, receipt_date, po_num, po_id in all_po_items:
            key = (mat_id, pl_id)
            if key not in po_items_map:
                po_items_map[key] = []
            po_items_map[key].append((qty, rec_qty, receipt_date, po_num, po_id))

        analysis_results = []

        # Check open PO items for these shortages in memory
        for (mat_id, pl_id), req in needed_components.items():
            po_items = po_items_map.get((mat_id, pl_id), [])

            coverage_qty = 0
            late_qty = 0
            coverage_pos = []

            for qty, rec_qty, receipt_date, po_num, po_id in po_items:
                rem = qty - rec_qty
                if rem <= 0:
                    continue
                
                is_late = False
                req_date = req["required_date"]
                # Normalize types to date for comparison if necessary
                if isinstance(receipt_date, date) and isinstance(req_date, date):
                    is_late = receipt_date > req_date
                elif isinstance(receipt_date, str) and isinstance(req_date, str):
                    is_late = receipt_date > req_date
                elif isinstance(receipt_date, date) and isinstance(req_date, str):
                    is_late = receipt_date.isoformat() > req_date
                elif isinstance(receipt_date, str) and isinstance(req_date, date):
                    is_late = receipt_date > req_date.isoformat()

                if is_late:
                    late_qty += rem
                else:
                    coverage_qty += rem
                
                coverage_pos.append({
                    "po_id": po_id,
                    "po_number": po_num,
                    "expected_receipt_date": receipt_date.isoformat() if isinstance(receipt_date, date) else receipt_date,
                    "quantity": rem,
                    "is_late": is_late
                })

            deficit = req["deficit"]
            total_supply_qty = coverage_qty + late_qty

            status = "NO_COVERAGE"
            if total_supply_qty > 0:
                if late_qty > 0 and coverage_qty < deficit:
                    status = "LATE_SUPPLY"
                elif total_supply_qty < deficit:
                    status = "PARTIAL_COVERAGE"
                else:
                    status = "FULL_COVERAGE"

            analysis_results.append({
                "material_id": mat_id,
                "material_code": req["material_code"],
                "material_name": req["material_name"],
                "plant_id": pl_id,
                "plant_name": req["plant_name"],
                "required_date": req["required_date"].isoformat() if isinstance(req["required_date"], date) else req["required_date"],
                "deficit": deficit,
                "status": status,
                "open_pos": coverage_pos,
                "coverage_quantity": coverage_qty,
                "late_quantity": late_qty,
                "impacted_orders": req["impacted_orders"]
            })

        return analysis_results
