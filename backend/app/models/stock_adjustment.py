"""Stock adjustment model."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class StockAdjustmentType(str, enum.Enum):
    """Stock adjustment type."""

    INCREASE = "increase"
    DECREASE = "decrease"


class StockAdjustment(Base):
    """Inventory adjustment record with immutable history."""

    __tablename__ = "stock_adjustments"
    __table_args__ = (
        Index("ix_stock_adjustments_material_id", "material_id"),
        Index("ix_stock_adjustments_plant_id", "plant_id"),
        Index("ix_stock_adjustments_created_at", "created_at"),
        Index(
            "ix_stock_adjustments_adjustment_reference",
            "adjustment_reference",
            unique=True,
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    adjustment_type = Column(
        SQLEnum(
            StockAdjustmentType,
            values_callable=lambda enum_cls: [
                member.value for member in enum_cls
            ],
            native_enum=False,
        ),
        nullable=False,
    )
    quantity = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    note = Column(Text, nullable=True)
    adjustment_reference = Column(String(100), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    material = relationship("Material", lazy="selectin")
    plant = relationship("Plant", lazy="selectin")
    user = relationship("User", lazy="selectin")

    def __repr__(self):
        return (
            f"<StockAdjustment {self.id}: {self.adjustment_type.value} "
            f"{self.quantity} for material {self.material_id} at "
            f"plant {self.plant_id}>"
        )
