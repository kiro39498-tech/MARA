"""Seed default warehouse for multi-warehouse support."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select  # noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.warehouse import Warehouse  # noqa: E402


async def seed_default_warehouse():
    """Create default warehouse if none exists."""
    async with AsyncSessionLocal() as db:
        try:
            # Check if warehouses exist
            result = await db.execute(select(Warehouse))
            existing = result.scalar_one_or_none()

            if existing:
                print(f"[OK] Warehouse already exists: {existing.name}")
                return

            # Create default warehouse
            warehouse = Warehouse(
                code="WH-MAIN",
                name="Main Warehouse",
                address="123 Main Street",
                city="Colombo",
                country="Sri Lanka",
                is_active=True,
            )

            db.add(warehouse)
            await db.commit()
            await db.refresh(warehouse)

            print(
                f"[OK] Created default warehouse: {warehouse.name} "
                f"(ID: {warehouse.id})"
            )

        except Exception as e:
            print(f"[ERROR] Error seeding warehouse: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_default_warehouse())
