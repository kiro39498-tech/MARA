"""Seed sample products and suppliers for testing purchases flow."""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select  # noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.product import Product, Category  # noqa: E402
from app.models.supplier import Supplier  # noqa: E402


async def seed_sample_data():
    """Create sample products and suppliers."""
    async with AsyncSessionLocal() as db:
        try:
            # Check if data already exists
            result = await db.execute(select(Product).limit(1))
            if result.scalar_one_or_none():
                print("[WARNING] Sample data already exists. Skipping seed.")
                return

            # Create default category
            category = Category(
                name="Electronics", description="Electronic products"
            )
            db.add(category)
            await db.flush()

            # Create 2 suppliers
            supplier1 = Supplier(
                code="SUP-001",
                name="Tech Solutions Ltd",
                contact_person="John Doe",
                email="john@techsolutions.com",
                phone="+94771234567",
                address_line1="45 Galle Road",
                city="Colombo",
                country="Sri Lanka",
                payment_terms="Net 30",
                is_active=True,
            )

            supplier2 = Supplier(
                code="SUP-002",
                name="Global Electronics Inc",
                contact_person="Jane Smith",
                email="jane@globalelec.com",
                phone="+94772345678",
                address_line1="78 Kandy Road",
                city="Kandy",
                country="Sri Lanka",
                payment_terms="Net 45",
                is_active=True,
            )

            db.add(supplier1)
            db.add(supplier2)
            await db.flush()

            # Create 3 products
            products = [
                Product(
                    sku="LAPTOP-001",
                    name="Dell Laptop XPS 15",
                    description="High-performance laptop with 16GB RAM",
                    category_id=category.id,
                    unit="pcs",
                    reorder_level=5,
                    reorder_quantity=10,
                    cost_price=80000.00,
                    selling_price=85000.00,
                    quantity=0,
                ),
                Product(
                    sku="MOUSE-001",
                    name="Logitech Wireless Mouse",
                    description="Ergonomic wireless mouse",
                    category_id=category.id,
                    unit="pcs",
                    reorder_level=10,
                    reorder_quantity=20,
                    cost_price=2000.00,
                    selling_price=2500.00,
                    quantity=0,
                ),
                Product(
                    sku="KB-001",
                    name="Mechanical Keyboard RGB",
                    description="RGB backlit mechanical keyboard",
                    category_id=category.id,
                    unit="pcs",
                    reorder_level=8,
                    reorder_quantity=15,
                    cost_price=6500.00,
                    selling_price=7500.00,
                    quantity=0,
                ),
            ]

            for product in products:
                db.add(product)

            await db.commit()

            print("[OK] Sample data seeded successfully:")
            print(f"   - Category: {category.name}")
            print(f"   - Suppliers: {supplier1.name}, {supplier2.name}")
            print(f"   - Products: {len(products)} items")

        except Exception as e:
            print(f"[ERROR] Error seeding sample data: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_sample_data())
