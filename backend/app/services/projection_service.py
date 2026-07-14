"""Projection Service."""

from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from app.models.inventory import Inventory
from app.models.material import Material
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.production_order import ProductionOrder
from app.models.bom import BillOfMaterials, BOMItem
from app.models.material_projection import MaterialProjection


class ProjectionService:
    """
    Computes time-phased material projections and shortage details.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_bom_components(self, material_id: int) -> dict[int, float]:
        """
        Explode the BOM for a given assembly material.
        Returns a dictionary of {component_id: qty_required_per_assembly_unit}.
        """
        stmt = select(BillOfMaterials).where(
            and_(
                BillOfMaterials.material_id == material_id,
                BillOfMaterials.is_active == True
            )
        )
        res = await self.db.execute(stmt)
        bom = res.scalar_one_or_none()

        if not bom:
            return {}

        components = {}
        for item in bom.items:
            components[item.component_id] = item.quantity
        return components

    async def calculate_projection(self, material_id: int, plant_id: int, horizon_days: int = 30) -> dict:
        """
        Calculate the day-by-day projected balance for a material at a plant.
        Formula: Projected Balance = Previous Balance + Incoming Supply - Production Demand.
        """
        today = date.today()
        end_date = today + timedelta(days=horizon_days)

        # 1. Get initial inventory
        stmt = select(Inventory).where(
            Inventory.material_id == material_id,
            Inventory.plant_id == plant_id
        )
        res = await self.db.execute(stmt)
        inv = res.scalar_one_or_none()
        initial_balance = inv.usable_inventory if inv else 0

        # 2. Get incoming Purchase Order Supply (expected receipt date)
        po_stmt = (
            select(PurchaseOrderItem.quantity, PurchaseOrderItem.received_quantity, PurchaseOrder.expected_receipt_date)
            .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
            .where(
                and_(
                    PurchaseOrderItem.material_id == material_id,
                    PurchaseOrder.plant_id == plant_id,
                    PurchaseOrder.status.in_(["DRAFT", "SENT", "PARTIALLY_RECEIVED"]),
                    PurchaseOrder.expected_receipt_date >= today,
                    PurchaseOrder.expected_receipt_date <= end_date
                )
            )
        )
        po_res = await self.db.execute(po_stmt)
        po_items = po_res.all()

        daily_supply = {}
        for qty, rec_qty, receipt_date in po_items:
            rem = qty - rec_qty
            if rem > 0:
                daily_supply[receipt_date] = daily_supply.get(receipt_date, 0) + rem

        # 3. Production order outputs (Supplies assembly on required date)
        assembly_stmt = select(ProductionOrder).where(
            and_(
                ProductionOrder.material_id == material_id,
                ProductionOrder.plant_id == plant_id,
                ProductionOrder.status.in_(["PLANNED", "IN_PROGRESS"]),
                ProductionOrder.required_date >= today,
                ProductionOrder.required_date <= end_date
            )
        )
        assembly_res = await self.db.execute(assembly_stmt)
        assembly_orders = assembly_res.scalars().all()

        for ao in assembly_orders:
            daily_supply[ao.required_date] = daily_supply.get(ao.required_date, 0) + ao.quantity

        # 4. Production order inputs (Consumes components on start date)
        # Find all production orders that consume this material as a component
        # To do this, find production orders at the plant, check their assembly BOMs, and see if this material is a component.
        po_demand_stmt = select(ProductionOrder).where(
            and_(
                ProductionOrder.plant_id == plant_id,
                ProductionOrder.status.in_(["PLANNED", "IN_PROGRESS"]),
                ProductionOrder.start_date >= today,
                ProductionOrder.start_date <= end_date
            )
        )
        po_demand_res = await self.db.execute(po_demand_stmt)
        plant_orders = po_demand_res.scalars().all()

        daily_demand = {}
        for order in plant_orders:
            components = await self.get_bom_components(order.material_id)
            if material_id in components:
                qty_needed = order.quantity * components[material_id]
                daily_demand[order.start_date] = daily_demand.get(order.start_date, 0.0) + qty_needed

        # 5. Calculate day-by-day projected balance
        projected_balance = initial_balance
        timeline = []
        first_shortage_date = None
        shortage_quantity = 0
        recovery_date = None
        days_of_coverage = horizon_days

        # Clear existing projections for this material and plant
        clear_stmt = delete(MaterialProjection).where(
            and_(
                MaterialProjection.material_id == material_id,
                MaterialProjection.plant_id == plant_id
            )
        )
        await self.db.execute(clear_stmt)

        for d in range(horizon_days):
            current_date = today + timedelta(days=d)
            supply = int(daily_supply.get(current_date, 0))
            demand = int(daily_demand.get(current_date, 0))

            projected_balance = projected_balance + supply - demand

            shortage_flag = projected_balance < 0

            # DB record
            db_proj = MaterialProjection(
                material_id=material_id,
                plant_id=plant_id,
                date=current_date,
                projected_balance=projected_balance,
                incoming_supply=supply,
                production_demand=demand,
                shortage_flag=shortage_flag
            )
            self.db.add(db_proj)

            timeline.append({
                "date": current_date,
                "projected_balance": projected_balance,
                "incoming_supply": supply,
                "production_demand": demand,
                "shortage_flag": shortage_flag
            })

            # Check coverage and shortages
            if shortage_flag:
                if first_shortage_date is None:
                    first_shortage_date = current_date
                    shortage_quantity = abs(projected_balance)
                    days_of_coverage = d
                elif first_shortage_date is not None and recovery_date is None:
                    # Update max shortage
                    shortage_quantity = max(shortage_quantity, abs(projected_balance))
            else:
                if first_shortage_date is not None and recovery_date is None:
                    recovery_date = current_date

        await self.db.flush()

        return {
            "material_id": material_id,
            "plant_id": plant_id,
            "horizon_days": horizon_days,
            "initial_balance": initial_balance,
            "timeline": timeline,
            "first_shortage_date": first_shortage_date,
            "shortage_quantity": shortage_quantity,
            "recovery_date": recovery_date,
            "days_of_coverage": days_of_coverage
        }
