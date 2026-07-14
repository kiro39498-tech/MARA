"""Plant Inventory model (replaces ProductLocation)."""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, event
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimeStampMixin


class Inventory(Base, TimeStampMixin):
    """
    Tracks inventory stock levels for a material at a specific manufacturing plant.
    """

    __tablename__ = "plant_inventory"
    __table_args__ = (
        UniqueConstraint(
            "material_id", "plant_id", name="uq_material_plant"
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

    # Stocks
    on_hand = Column(Integer, nullable=False, default=0)
    reserved = Column(Integer, nullable=False, default=0)
    blocked = Column(Integer, nullable=False, default=0)
    quality_hold = Column(Integer, nullable=False, default=0)
    in_transit = Column(Integer, nullable=False, default=0)

    # Policy thresholds
    safety_stock = Column(Integer, nullable=False, default=0)
    buffer_stock = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=0)

    # Calculated field - NEVER manually edited
    usable_inventory = Column(Integer, nullable=False, default=0)

    # Relationships
    material = relationship(
        "Material", back_populates="locations", lazy="selectin"
    )
    plant = relationship(
        "Plant", back_populates="stock_locations", lazy="selectin"
    )

    def calculate_usable(self):
        """Calculate usable inventory."""
        self.usable_inventory = (self.on_hand or 0) - (self.reserved or 0) - (self.blocked or 0) - (self.quality_hold or 0)

    def __repr__(self):
        return (
            f"<Inventory material_id={self.material_id} "
            f"plant_id={self.plant_id} usable={self.usable_inventory}>"
        )


# Event listeners to enforce deterministic usable inventory calculation
@event.listens_for(Inventory, 'before_insert')
def receive_before_insert(mapper, connection, target):
    target.calculate_usable()


@event.listens_for(Inventory, 'before_update')
def receive_before_update(mapper, connection, target):
    target.calculate_usable()
