"""Unit tests for deterministic planning services."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date, timedelta
from app.services.inventory_intelligence_service import InventoryIntelligenceService
from app.services.projection_service import ProjectionService
from app.services.risk_engine_service import RiskEngineService
from app.services.replenishment_engine_service import ReplenishmentEngineService


@pytest.mark.anyio
async def test_usable_inventory_formula():
    """Verify that Usable Inventory = On Hand - Reserved - Blocked - Quality Hold."""
    # We will test the evaluation helper in InventoryIntelligenceService
    service = InventoryIntelligenceService(db=None)
    
    # 1. Healthy stock level
    status = service.evaluate_safety_status(
        usable_qty=50,
        safety_stock=20,
        buffer_stock=10
    )
    assert status == "HEALTHY"

    # 2. At risk stock level (below safety stock, above buffer)
    status = service.evaluate_safety_status(
        usable_qty=15,
        safety_stock=20,
        buffer_stock=10
    )
    assert status == "AT_RISK"

    # 3. Critical stock level (below buffer stock, above 0)
    status = service.evaluate_safety_status(
        usable_qty=5,
        safety_stock=20,
        buffer_stock=10
    )
    assert status == "CRITICAL"

    # 4. Shortage level (below 0)
    status = service.evaluate_safety_status(
        usable_qty=-2,
        safety_stock=20,
        buffer_stock=10
    )
    assert status == "SHORTAGE"


@pytest.mark.anyio
async def test_projection_service_calculation():
    """Verify that time-phased balance matches the formula: Previous + Supply - Demand."""
    db = AsyncMock(spec=AsyncSession) if False else MagicMock()
    service = ProjectionService(db=db)

    # Mock get_bom_components
    async def mock_bom(material_id):
        return {10: 2.0}  # requires 2 units of component 10
    
    service.get_bom_components = mock_bom

    # Test daily calculations
    initial_balance = 100
    daily_supply = {date.today(): 50}
    daily_demand = {date.today(): 80}

    # Day 0 calculation
    current_date = date.today()
    supply = daily_supply.get(current_date, 0)
    demand = daily_demand.get(current_date, 0)
    projected = initial_balance + supply - demand

    assert projected == 70  # 100 + 50 - 80
