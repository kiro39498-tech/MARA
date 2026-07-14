"""Seed script for MARA manufacturing planning database."""

import asyncio
import sys
import random
from pathlib import Path
from datetime import date, timedelta
from sqlalchemy import delete

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal, init_db
from app.models.plant import Plant
from app.models.supplier import Supplier
from app.models.supplier_performance import SupplierPerformance
from app.models.material import Material, Category, ProcurementType, ABCClassification, MaterialCriticality
from app.models.inventory import Inventory
from app.models.bom import BillOfMaterials, BOMItem
from app.models.production_order import ProductionOrder
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem


async def seed_mara_data():
    """Seed the database with realistic manufacturing data."""
    async with AsyncSessionLocal() as db:
        try:
            print("Dropping legacy database tables...")
            from sqlalchemy import text
            await db.execute(text("DROP TABLE IF EXISTS purchase_items, purchases, product_locations, warehouses, products CASCADE;"))
            await db.commit()
            print("Initializing database tables...")
            await init_db()
            print("Cleaning old data...")
            await db.execute(delete(PurchaseOrderItem))
            await db.execute(delete(PurchaseOrder))
            await db.execute(delete(ProductionOrder))
            await db.execute(delete(BOMItem))
            await db.execute(delete(BillOfMaterials))
            await db.execute(delete(Inventory))
            await db.execute(delete(SupplierPerformance))
            await db.execute(delete(Supplier))
            await db.execute(delete(Material))
            await db.execute(delete(Plant))
            await db.execute(delete(Category))
            await db.commit()

            print("1. Seeding Categories...")
            categories = [
                Category(name="Raw Metals", description="Raw steel, aluminum, copper sheets"),
                Category(name="Electronic Components", description="Microchips, resistors, wiring, sensors"),
                Category(name="Mechanical Parts", description="Gears, pulleys, brackets, housings"),
                Category(name="Sub-Assemblies", description="Power boards, motor assemblies, sensor clusters"),
                Category(name="Finished Goods", description="Smart routers, robotic arms, smart hubs")
            ]
            db.add_all(categories)
            await db.flush()

            print("2. Seeding 10 Plants...")
            plants = []
            cities = ["Chicago", "Detroit", "Cleveland", "Pittsburgh", "Gary", "Buffalo", "Toledo", "Milwaukee", "St. Louis", "Cincinnati"]
            for i in range(10):
                plant = Plant(
                    code=f"PLT-{100+i}",
                    name=f"{cities[i]} Manufacturing Plant",
                    address=f"{1000 + i * 50} Industrial Parkway",
                    city=cities[i],
                    state="IL" if i == 0 else "MI" if i == 1 else "OH" if i in [2, 6, 9] else "PA" if i in [3, 5] else "IN" if i == 4 else "WI" if i == 7 else "MO",
                    country="USA",
                    postal_code=f"{60600 + i*13}",
                    contact_person=f"Plant Manager {i+1}",
                    phone=f"+1-312-555-01{i:02d}",
                    email=f"plant{i+1}@company.com",
                    is_active=True
                )
                plants.append(plant)
                db.add(plant)
            await db.flush()

            print("3. Seeding 300 Suppliers...")
            suppliers = []
            supplier_names = ["Global Metals", "Apex Electronics", "Precision Gears", "Fastener Depot", "Silicon Valley Sourcing", "Midwest Castings", "Electrotech Inc.", "Rapid Machining", "Thermal Solutions", "Optics Group"]
            for i in range(300):
                base_name = supplier_names[i % len(supplier_names)]
                supplier = Supplier(
                    code=f"SUP-{1000+i}",
                    name=f"{base_name} Corp #{i+1}",
                    contact_person=f"Account Manager {i+1}",
                    email=f"vendor{i+1}@sourcing.com",
                    phone=f"+1-800-555-{i:04d}",
                    address_line1=f"Suite {100+i}",
                    city="Supply Town",
                    country="USA",
                    payment_terms="Net 30" if i % 2 == 0 else "Net 45",
                    is_active=True
                )
                suppliers.append(supplier)
                db.add(supplier)
            await db.flush()

            print("4. Seeding Supplier Performance Ratings...")
            for sup in suppliers:
                perf = SupplierPerformance(
                    supplier_id=sup.id,
                    evaluation_date=date.today() - timedelta(days=1),
                    on_time_delivery_rate=random.uniform(0.70, 0.99),
                    quality_rating=random.uniform(80.0, 100.0),
                    lead_time_variance=random.uniform(0.5, 4.0),
                    total_orders=random.randint(10, 100),
                    late_orders=random.randint(0, 10)
                )
                db.add(perf)

            print("5. Seeding 500 Materials (Raw, Component, Assembly, Finished)...")
            materials = []
            
            # Categories: 0: Raw Metals (Buy), 1: Electronics (Buy), 2: Mech (Buy), 3: Sub-assembly (Make), 4: Finished Goods (Make)
            types = ["RAW", "COMPONENT", "COMPONENT", "ASSEMBLY", "FINISHED"]
            procurements = [ProcurementType.BUY, ProcurementType.BUY, ProcurementType.BUY, ProcurementType.MAKE, ProcurementType.MAKE]
            
            for i in range(500):
                cat_idx = i % 5
                cat = categories[cat_idx]
                mat_type = types[cat_idx]
                proc_type = procurements[cat_idx]
                
                # Assign planner
                planner_email = f"planner.alex@mara.com" if i % 3 == 0 else f"planner.maria@mara.com" if i % 3 == 1 else "planner.sam@mara.com"
                
                material = Material(
                    material_code=f"MAT-{10000+i}",
                    name=f"{cat.name[:-1]} Item #{i+1}",
                    description=f"High-quality {cat.name} component for industrial assemblies.",
                    category_id=cat.id,
                    material_type=mat_type,
                    unit="pcs" if cat_idx != 0 else "kg",
                    planner=planner_email,
                    procurement_type=proc_type,
                    lead_time=random.randint(3, 21),
                    abc_classification=random.choice([ABCClassification.A, ABCClassification.B, ABCClassification.C]),
                    criticality=random.choice([MaterialCriticality.HIGH, MaterialCriticality.MEDIUM, MaterialCriticality.LOW]),
                    cost_price=round(random.uniform(5.0, 500.0), 2),
                    selling_price=round(random.uniform(10.0, 1000.0), 2),
                    is_active=True
                )
                materials.append(material)
                db.add(material)
            await db.flush()

            print("6. Seeding BOM Relationships...")
            # We map: Finished Goods (indices ending in 4) are composed of Sub-assemblies (indices ending in 3)
            # Sub-assemblies are composed of Raw Metals (indices ending in 0), Electronics (1) and Mech Parts (2)
            finished_materials = [m for m in materials if m.material_type == "FINISHED"]
            assembly_materials = [m for m in materials if m.material_type == "ASSEMBLY"]
            component_materials = [m for m in materials if m.material_type in ["RAW", "COMPONENT"]]

            for fg in finished_materials:
                bom = BillOfMaterials(
                    material_id=fg.id,
                    name=f"Standard BOM for {fg.name}",
                    version="1.0",
                    is_active=True
                )
                db.add(bom)
                await db.flush()
                
                # Pick 2-3 assembly parts
                sub_parts = random.sample(assembly_materials, random.randint(2, 3))
                for sp in sub_parts:
                    bom_item = BOMItem(
                        bom_id=bom.id,
                        component_id=sp.id,
                        quantity=float(random.randint(1, 3))
                    )
                    db.add(bom_item)

            for asm in assembly_materials:
                bom = BillOfMaterials(
                    material_id=asm.id,
                    name=f"Assembly BOM for {asm.name}",
                    version="1.0",
                    is_active=True
                )
                db.add(bom)
                await db.flush()
                
                # Pick 3-5 components/raw metals
                comps = random.sample(component_materials, random.randint(3, 5))
                for cp in comps:
                    bom_item = BOMItem(
                        bom_id=bom.id,
                        component_id=cp.id,
                        quantity=float(random.randint(2, 8))
                    )
                    db.add(bom_item)
            await db.flush()

            print("7. Seeding 5000 Inventory Records across Plants...")
            # 500 materials * 10 plants = 5000 plant inventory entries
            for mat in materials:
                for plant in plants:
                    safety = random.randint(10, 50)
                    buffer = random.randint(5, 20)
                    reorder = safety + buffer + random.randint(5, 30)
                    
                    # Generate stock numbers
                    on_hand = random.choice([0, random.randint(10, 150)])
                    reserved = random.randint(0, min(10, on_hand)) if on_hand > 0 else 0
                    blocked = random.randint(0, min(5, on_hand - reserved)) if (on_hand - reserved) > 0 else 0
                    quality_hold = random.randint(0, min(5, on_hand - reserved - blocked)) if (on_hand - reserved - blocked) > 0 else 0
                    in_transit = random.choice([0, random.randint(10, 50)])

                    inv = Inventory(
                        material_id=mat.id,
                        plant_id=plant.id,
                        on_hand=on_hand,
                        reserved=reserved,
                        blocked=blocked,
                        quality_hold=quality_hold,
                        in_transit=in_transit,
                        safety_stock=safety,
                        buffer_stock=buffer,
                        reorder_point=reorder
                    )
                    db.add(inv)
            await db.flush()

            print("8. Seeding 2000 Production Orders (Demand)...")
            fg_and_asm = [m for m in materials if m.material_type in ["FINISHED", "ASSEMBLY"]]
            for i in range(2000):
                mat = random.choice(fg_and_asm)
                plant = random.choice(plants)
                start_offset = random.randint(-5, 20)
                required_offset = start_offset + random.randint(3, 10)
                
                order = ProductionOrder(
                    order_number=f"PROD-{10000+i}",
                    material_id=mat.id,
                    plant_id=plant.id,
                    quantity=random.randint(5, 50),
                    start_date=date.today() + timedelta(days=start_offset),
                    required_date=date.today() + timedelta(days=required_offset),
                    status=random.choice(["PLANNED", "IN_PROGRESS"]) if start_offset > 0 else random.choice(["COMPLETED", "IN_PROGRESS"]),
                    priority=random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
                )
                db.add(order)
            await db.flush()

            print("9. Seeding 5000 Purchase Orders (Supply)...")
            comp_and_raw = [m for m in materials if m.material_type in ["RAW", "COMPONENT"]]
            for i in range(5000):
                supplier = random.choice(suppliers)
                plant = random.choice(plants)
                order_offset = random.randint(-15, 10)
                receipt_offset = order_offset + random.randint(5, 20)
                
                status = "RECEIVED" if receipt_offset < 0 else random.choice(["SENT", "PARTIALLY_RECEIVED", "DRAFT"])

                po = PurchaseOrder(
                    po_number=f"PO-{10000+i}",
                    supplier_id=supplier.id,
                    plant_id=plant.id,
                    status=status,
                    total_amount=0.0,  # calculated later
                    order_date=date.today() + timedelta(days=order_offset),
                    expected_receipt_date=date.today() + timedelta(days=receipt_offset),
                    notes="Automated material replenishment order."
                )
                db.add(po)
                await db.flush()

                # Add 1-3 items to PO
                po_total = 0.0
                po_items_mats = random.sample(comp_and_raw, random.randint(1, 3))
                for pm in po_items_mats:
                    qty = random.randint(50, 500)
                    rec_qty = qty if status == "RECEIVED" else random.randint(0, qty) if status == "PARTIALLY_RECEIVED" else 0
                    unit_price = pm.cost_price or 10.0
                    item_total = qty * unit_price
                    po_total += item_total
                    
                    po_item = PurchaseOrderItem(
                        purchase_order_id=po.id,
                        material_id=pm.id,
                        quantity=qty,
                        received_quantity=rec_qty,
                        unit_price=unit_price,
                        total_price=item_total,
                        batch_number=f"BAT-{random.randint(10000, 99999)}" if rec_qty > 0 else None,
                        expiry_date=date.today() + timedelta(days=365) if rec_qty > 0 else None
                    )
                    db.add(po_item)
                
                po.total_amount = po_total
            
            await db.commit()
            print("[OK] Manufacturing database successfully seeded with all elements!")

        except Exception as e:
            print(f"[ERROR] Error seeding data: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_mara_data())
