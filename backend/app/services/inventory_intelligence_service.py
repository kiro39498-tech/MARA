"""Inventory Intelligence Service."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.inventory import Inventory
from app.models.material import Material
from app.models.plant import Plant


class InventoryIntelligenceService:
    """
    Evaluates inventory counts against safety stock, buffer stock, and reorder levels.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def evaluate_safety_status(self, usable_qty: int, safety_stock: int, buffer_stock: int) -> str:
        """
        Classifies stock level safety status based on deterministic thresholds.
        """
        if usable_qty <= 0:
            return "SHORTAGE"
        elif usable_qty <= buffer_stock:
            return "CRITICAL"
        elif usable_qty <= safety_stock:
            return "AT_RISK"
        else:
            return "HEALTHY"

    async def get_material_health_at_plant(self, material_id: int, plant_id: int) -> dict:
        """
        Return the inventory quantities and safety stock status of a material at a plant.
        """
        stmt = select(Inventory).where(
            Inventory.material_id == material_id,
            Inventory.plant_id == plant_id
        )
        res = await self.db.execute(stmt)
        inv = res.scalar_one_or_none()

        if not inv:
            return {
                "material_id": material_id,
                "plant_id": plant_id,
                "on_hand": 0,
                "reserved": 0,
                "blocked": 0,
                "quality_hold": 0,
                "in_transit": 0,
                "safety_stock": 0,
                "buffer_stock": 0,
                "reorder_point": 0,
                "usable_inventory": 0,
                "status": "SHORTAGE"
            }

        status = self.evaluate_safety_status(
            inv.usable_inventory,
            inv.safety_stock,
            inv.buffer_stock
        )

        return {
            "material_id": inv.material_id,
            "plant_id": inv.plant_id,
            "on_hand": inv.on_hand,
            "reserved": inv.reserved,
            "blocked": inv.blocked,
            "quality_hold": inv.quality_hold,
            "in_transit": inv.in_transit,
            "safety_stock": inv.safety_stock,
            "buffer_stock": inv.buffer_stock,
            "reorder_point": inv.reorder_point,
            "usable_inventory": inv.usable_inventory,
            "status": status
        }

    async def get_all_inventory_health(self) -> list[dict]:
        """
        Return the health status of all inventory records in the system.
        """
        stmt = select(Inventory)
        res = await self.db.execute(stmt)
        records = res.scalars().all()

        results = []
        for r in records:
            status = self.evaluate_safety_status(
                r.usable_inventory,
                r.safety_stock,
                r.buffer_stock
            )
            results.append({
                "id": r.id,
                "material_id": r.material_id,
                "material_code": r.material.material_code if r.material else "N/A",
                "material_name": r.material.name if r.material else "N/A",
                "plant_id": r.plant_id,
                "plant_name": r.plant.name if r.plant else "N/A",
                "on_hand": r.on_hand,
                "reserved": r.reserved,
                "blocked": r.blocked,
                "quality_hold": r.quality_hold,
                "in_transit": r.in_transit,
                "safety_stock": r.safety_stock,
                "buffer_stock": r.buffer_stock,
                "reorder_point": r.reorder_point,
                "usable_inventory": r.usable_inventory,
                "status": status
            })
        return results
