"""Notification service with source sync and read-state operations."""

from datetime import datetime
from typing import Any

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.product import Product, StockStatus


class NotificationService:
    """Manages persisted notifications per user."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_for_user(
        self, user_id: int, source_limit: int = 20
    ) -> None:
        """Build/refresh notifications from live business data sources."""
        activity_rows = await self.db.execute(
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(source_limit)
        )
        activities = activity_rows.scalars().all()

        from app.models.inventory import Inventory
        from app.models.material import Material

        low_stock_rows = await self.db.execute(
            select(Inventory)
            .join(Material, Inventory.material_id == Material.id)
            .where(
                (Inventory.on_hand - Inventory.reserved - Inventory.blocked - Inventory.quality_hold) <= Inventory.safety_stock
            )
            .order_by(Inventory.updated_at.desc())
            .limit(source_limit)
        )
        low_stock_items = low_stock_rows.scalars().all()

        for activity in activities:
            source_key = f"activity:{activity.id}"
            payload = {
                "title": (activity.action or "Activity").title(),
                "message": activity.description
                or f"{activity.resource_type} updated",
                "type": self._map_activity_type(activity.action or ""),
                "action_url": self._resource_to_url(
                    activity.resource_type or ""
                ),
                "source_type": "activity",
                "source_id": str(activity.id),
                "source_key": source_key,
                "created_at": activity.created_at,
            }
            await self._upsert_notification(
                user_id=user_id, source_key=source_key, payload=payload
            )

        for inv in low_stock_items:
            source_key = f"low_stock:{inv.id}"
            created_at = inv.updated_at or datetime.utcnow()
            payload = {
                "title": "Low Stock Alert",
                "message": (
                    f"Material {inv.material.name} is at {inv.on_hand} units at plant {inv.plant.name} "
                    f"(safety stock is {inv.safety_stock})."
                ),
                "type": "warning",
                "action_url": "/materials",
                "source_type": "low_stock",
                "source_id": str(inv.id),
                "source_key": source_key,
                "created_at": created_at,
            }
            await self._upsert_notification(
                user_id=user_id, source_key=source_key, payload=payload
            )

        await self.db.commit()

    async def list_for_user(
        self, user_id: int, limit: int = 20
    ) -> tuple[list[Notification], int]:
        """Return latest notifications and unread count."""
        rows = await self.db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        items = rows.scalars().all()

        unread_result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        unread_count = unread_result.scalar_one() or 0
        return items, unread_count

    async def mark_read(self, user_id: int, notification_id: int) -> bool:
        """Mark a single notification as read for the user."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        item = result.scalar_one_or_none()
        if item is None:
            return False

        item.is_read = True
        item.read_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def mark_all_read(self, user_id: int) -> None:
        """Mark all notifications as read for the user."""
        await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        await self.db.commit()

    async def _upsert_notification(
        self, user_id: int, source_key: str, payload: dict[str, Any]
    ) -> None:
        existing_result = await self.db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.source_key == source_key,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing is None:
            self.db.add(
                Notification(
                    user_id=user_id,
                    title=payload["title"],
                    message=payload["message"],
                    type=payload["type"],
                    action_url=payload["action_url"],
                    source_type=payload["source_type"],
                    source_id=payload["source_id"],
                    source_key=payload["source_key"],
                    created_at=payload["created_at"],
                )
            )
            return

        existing.title = payload["title"]
        existing.message = payload["message"]
        existing.type = payload["type"]
        existing.action_url = payload["action_url"]
        existing.created_at = payload["created_at"]

    @staticmethod
    def _resource_to_url(resource_type: str) -> str | None:
        normalized = resource_type.lower()
        mapping = {
            "product": "/products",
            "products": "/products",
            "sale": "/sales",
            "sales": "/sales",
            "purchase": "/purchases",
            "purchases": "/purchases",
            "customer": "/customers",
            "customers": "/customers",
            "supplier": "/suppliers",
            "suppliers": "/suppliers",
            "warehouse": "/warehouses",
            "warehouses": "/warehouses",
            "stock_adjustment": "/stock-adjustments",
            "user": "/users",
        }
        return mapping.get(normalized)

    @staticmethod
    def _map_activity_type(action: str) -> str:
        lowered = action.lower()
        if "delete" in lowered or "cancel" in lowered or "fail" in lowered:
            return "error"
        if (
            "create" in lowered
            or "receive" in lowered
            or "complete" in lowered
        ):
            return "success"
        if "update" in lowered or "adjust" in lowered:
            return "warning"
        return "info"
