"""Warehouse service for warehouse management."""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_location import ProductLocation
from app.models.purchase import Purchase
from app.models.sale import Sale
from app.models.stock_ledger import StockLedger
from app.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate
from app.services.base_service import BaseService


class WarehouseService(
    BaseService[Warehouse, WarehouseCreate, WarehouseUpdate]
):
    """Warehouse service with search/filter and delete safety checks."""

    def __init__(self, db: AsyncSession):
        super().__init__(Warehouse, db)

    async def get_by_code(self, code: str) -> Optional[Warehouse]:
        """Get warehouse by unique code."""
        result = await self.db.execute(
            select(Warehouse).where(
                func.lower(Warehouse.code) == code.strip().lower()
            )
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Warehouse], int]:
        """Get warehouses with pagination and optional filters."""
        query = select(Warehouse)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Warehouse.name.ilike(search_term),
                    Warehouse.code.ilike(search_term),
                    Warehouse.city.ilike(search_term),
                )
            )

        if is_active is not None:
            query = query.where(Warehouse.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = (
            query.order_by(Warehouse.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total or 0

    async def has_code_conflict(
        self, code: str, exclude_id: Optional[int] = None
    ) -> bool:
        """Check if a warehouse code already exists.

        Optionally excludes one warehouse ID.
        """
        if self.db is None:
            return False
        query = select(Warehouse).where(
            func.lower(Warehouse.code) == code.strip().lower()
        )
        if exclude_id is not None:
            query = query.where(Warehouse.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def has_dependencies(self, warehouse_id: int) -> bool:
        """Check whether warehouse is referenced by inventory or
        transactions."""
        checks = [
            select(func.count())
            .select_from(ProductLocation)
            .where(ProductLocation.warehouse_id == warehouse_id),
            select(func.count())
            .select_from(StockLedger)
            .where(StockLedger.warehouse_id == warehouse_id),
            select(func.count())
            .select_from(Purchase)
            .where(Purchase.warehouse_id == warehouse_id),
            select(func.count())
            .select_from(Sale)
            .where(Sale.warehouse_id == warehouse_id),
        ]

        for check in checks:
            count = await self.db.scalar(check)
            if (count or 0) > 0:
                return True

        return False
