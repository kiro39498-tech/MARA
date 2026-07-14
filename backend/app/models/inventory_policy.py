"""Inventory Policy model."""

from sqlalchemy import Column, Integer, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimeStampMixin


class InventoryPolicy(Base, TimeStampMixin):
    """
    Defines inventory replenishment rules and levels for a specific material and plant.
    """

    __tablename__ = "inventory_policies"
    __table_args__ = (
        UniqueConstraint(
            "material_id", "plant_id", name="uq_policy_material_plant"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(
        Integer,
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plant_id = Column(
        Integer,
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Policy levels
    safety_stock = Column(Integer, nullable=False, default=0)
    buffer_stock = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=0)
    lead_time_days = Column(Integer, nullable=False, default=7)
    service_level = Column(Float, nullable=False, default=0.95)  # e.g., 95% target service level

    # Relationships
    material = relationship("Material", lazy="selectin")
    plant = relationship("Plant", lazy="selectin")

    def __repr__(self):
        return f"<InventoryPolicy material_id={self.material_id} plant_id={self.plant_id}>"
