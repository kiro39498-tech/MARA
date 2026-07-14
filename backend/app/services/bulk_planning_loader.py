from datetime import date, timedelta
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inventory import Inventory
from app.models.material import Material
from app.models.plant import Plant
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.production_order import ProductionOrder
from app.models.bom import BillOfMaterials, BOMItem

class BulkPlanningData:
    """
    Bulk loads all active inventory, BOMs, POs, and Production Orders into memory
    to allow ultra-fast O(1) in-memory calculation of projections and shortages.
    """
    def __init__(self, db: AsyncSession, horizon_days: int = 30):
        self.db = db
        self.horizon_days = horizon_days
        self.today = date.today()
        self.end_date = self.today + timedelta(days=horizon_days)
        
        self.inventories = []
        self.inventory_map = {}
        self.bom_map = {}
        self.bom_components_map = {}
        self.po_items = []
        self.po_supply_map = {}
        self.production_orders = []
        self.plant_production_orders = {}
        self.ao_supply_map = {}

    async def load_all(self) -> "BulkPlanningData":
        # 1. Load all inventories
        inv_stmt = select(Inventory).options(
            joinedload(Inventory.material),
            joinedload(Inventory.plant)
        )
        inv_res = await self.db.execute(inv_stmt)
        self.inventories = inv_res.scalars().all()
        self.inventory_map = {
            (inv.material_id, inv.plant_id): inv
            for inv in self.inventories
        }

        # 2. Load all active BOMs
        bom_stmt = select(BillOfMaterials).where(BillOfMaterials.is_active == True).options(
            selectinload(BillOfMaterials.items)
        )
        bom_res = await self.db.execute(bom_stmt)
        boms = bom_res.scalars().all()
        self.bom_map = {b.material_id: b.items for b in boms}
        
        self.bom_components_map = {}
        for b in boms:
            self.bom_components_map[b.material_id] = {item.component_id: item.quantity for item in b.items}

        # 3. Load all open PO items
        po_stmt = (
            select(
                PurchaseOrderItem.material_id,
                PurchaseOrderItem.quantity,
                PurchaseOrderItem.received_quantity,
                PurchaseOrder.plant_id,
                PurchaseOrder.expected_receipt_date,
                PurchaseOrder.po_number,
                PurchaseOrder.status
            )
            .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
            .where(
                and_(
                    PurchaseOrder.status.in_(["DRAFT", "SENT", "PARTIALLY_RECEIVED"]),
                    PurchaseOrder.expected_receipt_date >= self.today,
                    PurchaseOrder.expected_receipt_date <= self.end_date
                )
            )
        )
        po_res = await self.db.execute(po_stmt)
        self.po_items = po_res.all()

        self.po_supply_map = {}
        for mat_id, qty, rec_qty, plant_id, receipt_date, po_number, status in self.po_items:
            rem = qty - rec_qty
            if rem > 0:
                key = (mat_id, plant_id)
                if key not in self.po_supply_map:
                    self.po_supply_map[key] = []
                self.po_supply_map[key].append({
                    "quantity": rem,
                    "receipt_date": receipt_date,
                    "po_number": po_number,
                    "expected_receipt_date": receipt_date,
                    "status": status
                })

        # 4. Load all open Production Orders
        prod_stmt = select(ProductionOrder).where(
            ProductionOrder.status.in_(["PLANNED", "IN_PROGRESS"])
        ).options(
            joinedload(ProductionOrder.material),
            joinedload(ProductionOrder.plant)
        )
        prod_res = await self.db.execute(prod_stmt)
        self.production_orders = prod_res.scalars().all()

        self.plant_production_orders = {}
        self.ao_supply_map = {}
        
        for order in self.production_orders:
            # Plant orders (demand side)
            if order.plant_id not in self.plant_production_orders:
                self.plant_production_orders[order.plant_id] = []
            self.plant_production_orders[order.plant_id].append(order)
            
            # Assembly orders (supply side)
            if order.required_date >= self.today and order.required_date <= self.end_date:
                key = (order.material_id, order.plant_id)
                if key not in self.ao_supply_map:
                    self.ao_supply_map[key] = []
                self.ao_supply_map[key].append(order)

        return self

    def calculate_projection_in_memory(self, material_id: int, plant_id: int) -> dict:
        inv = self.inventory_map.get((material_id, plant_id))
        initial_balance = inv.usable_inventory if inv else 0

        # Daily supplies
        daily_supply = {}
        po_supplies = self.po_supply_map.get((material_id, plant_id), [])
        for item in po_supplies:
            rdate = item["receipt_date"]
            daily_supply[rdate] = daily_supply.get(rdate, 0) + item["quantity"]

        ao_supplies = self.ao_supply_map.get((material_id, plant_id), [])
        for order in ao_supplies:
            daily_supply[order.required_date] = daily_supply.get(order.required_date, 0) + order.quantity

        # Daily demands
        daily_demand = {}
        plant_orders = self.plant_production_orders.get(plant_id, [])
        for order in plant_orders:
            if order.start_date >= self.today and order.start_date <= self.end_date:
                components = self.bom_components_map.get(order.material_id, {})
                if material_id in components:
                    qty_needed = order.quantity * components[material_id]
                    daily_demand[order.start_date] = daily_demand.get(order.start_date, 0.0) + qty_needed

        # Project balance
        projected_balance = initial_balance
        timeline = []
        first_shortage_date = None
        shortage_quantity = 0
        days_of_coverage = self.horizon_days

        for d in range(self.horizon_days):
            current_date = self.today + timedelta(days=d)
            supply = int(daily_supply.get(current_date, 0))
            demand = int(daily_demand.get(current_date, 0))

            projected_balance = projected_balance + supply - demand

            if projected_balance < 0:
                if first_shortage_date is None:
                    first_shortage_date = current_date
                    days_of_coverage = d
                deficit = abs(projected_balance)
                if deficit > shortage_quantity:
                    shortage_quantity = deficit

            timeline.append({
                "date": current_date,
                "incoming_supply": supply,
                "production_demand": demand,
                "projected_balance": projected_balance,
                "is_shortage": projected_balance < 0
            })

        return {
            "material_id": material_id,
            "plant_id": plant_id,
            "initial_balance": initial_balance,
            "first_shortage_date": first_shortage_date,
            "shortage_quantity": shortage_quantity,
            "days_of_coverage": days_of_coverage,
            "timeline": timeline
        }
