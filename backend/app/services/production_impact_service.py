"""Production Impact Service."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload, selectinload
from app.models.bom import BillOfMaterials, BOMItem
from app.models.production_order import ProductionOrder
from app.models.inventory import Inventory


class ProductionImpactService:
    """
    Analyzes Bill Of Materials (BOM) explosions and maps component shortages to production orders.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def explode_bom_recursive(
        self, material_id: int, quantity: float = 1.0, level: int = 1, visited: set = None
    ) -> list[dict]:
        """
        Recursively explodes the Bill of Materials for a material.
        Protects against infinite recursion with a visited set.
        """
        if visited is None:
            visited = set()
        if material_id in visited:
            return []
        visited.add(material_id)

        stmt = select(BillOfMaterials).where(
            and_(
                BillOfMaterials.material_id == material_id,
                BillOfMaterials.is_active == True
            )
        ).options(selectinload(BillOfMaterials.items))
        res = await self.db.execute(stmt)
        bom = res.scalar_one_or_none()

        if not bom:
            return []

        exploded = []
        for item in bom.items:
            total_qty = quantity * item.quantity
            exploded.append({
                "component_id": item.component_id,
                "quantity": total_qty,
                "level": level
            })
            # Recurse down
            sub_exploded = await self.explode_bom_recursive(
                item.component_id, total_qty, level + 1, visited.copy()
            )
            exploded.extend(sub_exploded)

        return exploded

    async def get_impacted_production_orders(self, plant_id: int = None) -> list[dict]:
        """
        Check all pending production orders and identify which ones are delayed or impacted by raw material shortages.
        Optimized with bulk loading to avoid N+1 query loops.
        """
        # 1. Eagerly load BOMs and Inventory
        from app.services.bulk_planning_loader import BulkPlanningData
        bulk_data = BulkPlanningData(self.db)
        await bulk_data.load_all()

        # 2. Get production orders
        po_stmt = select(ProductionOrder).where(
            ProductionOrder.status.in_(["PLANNED", "IN_PROGRESS"])
        ).options(
            joinedload(ProductionOrder.material),
            joinedload(ProductionOrder.plant)
        )
        if plant_id:
            po_stmt = po_stmt.where(ProductionOrder.plant_id == plant_id)

        po_res = await self.db.execute(po_stmt)
        orders = po_res.scalars().all()

        impacted_orders = []

        # Local recursive BOM explosion helper utilizing bulk data
        def explode_in_memory(mat_id: int, qty: float, level: int = 1, visited: set = None) -> list[dict]:
            if visited is None:
                visited = set()
            if mat_id in visited:
                return []
            visited.add(mat_id)

            components = bulk_data.bom_components_map.get(mat_id, {})
            if not components:
                return []

            exploded = []
            for comp_id, unit_qty in components.items():
                total_qty = qty * unit_qty
                exploded.append({
                    "component_id": comp_id,
                    "quantity": total_qty,
                    "level": level
                })
                sub = explode_in_memory(comp_id, total_qty, level + 1, visited.copy())
                exploded.extend(sub)
            return exploded

        for order in orders:
            requirements = explode_in_memory(order.material_id, float(order.quantity))

            if not requirements:
                # Direct check of material availability
                inv = bulk_data.inventory_map.get((order.material_id, order.plant_id))
                usable = inv.usable_inventory if inv else 0
                if usable < order.quantity:
                    impacted_orders.append({
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "material_id": order.material_id,
                        "material_code": order.material.material_code if order.material else "N/A",
                        "material_name": order.material.name if order.material else "N/A",
                        "plant_id": order.plant_id,
                        "plant_name": order.plant.name if order.plant else "N/A",
                        "quantity": order.quantity,
                        "required_date": order.required_date,
                        "priority": order.priority,
                        "status": order.status,
                        "shortage_reason": f"Finished good stock low: need {order.quantity}, have {usable}"
                    })
                continue

            shortages = []
            for req in requirements:
                comp_id = req["component_id"]
                req_qty = req["quantity"]

                inv = bulk_data.inventory_map.get((comp_id, order.plant_id))
                usable = inv.usable_inventory if inv else 0

                if usable < req_qty:
                    shortages.append({
                        "component_id": comp_id,
                        "component_code": inv.material.material_code if inv and inv.material else f"MAT-{comp_id}",
                        "component_name": inv.material.name if inv and inv.material else "N/A",
                        "required": req_qty,
                        "available": usable,
                        "deficit": req_qty - usable
                    })

            if shortages:
                impacted_orders.append({
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "material_id": order.material_id,
                    "material_code": order.material.material_code if order.material else "N/A",
                    "material_name": order.material.name if order.material else "N/A",
                    "plant_id": order.plant_id,
                    "plant_name": order.plant.name if order.plant else "N/A",
                    "quantity": order.quantity,
                    "required_date": order.required_date,
                    "priority": order.priority,
                    "status": order.status,
                    "shortages": shortages,
                    "shortage_reason": f"Missing component {shortages[0]['component_code']} (deficit: {shortages[0]['deficit']})"
                })

        return impacted_orders
