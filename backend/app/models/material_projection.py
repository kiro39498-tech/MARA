"""Material Projection model."""

from sqlalchemy import Column, Integer, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimeStampMixin


class MaterialProjection(Base, TimeStampMixin):
    """
    Stores day-by-day material availability projections for a plant.
    """

    __tablename__ = "material_projections"

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
    date = Column(Date, nullable=False, index=True)
    projected_balance = Column(Integer, nullable=False, default=0)
    incoming_supply = Column(Integer, nullable=False, default=0)
    production_demand = Column(Integer, nullable=False, default=0)
    shortage_flag = Column(Boolean, nullable=False, default=False)

    # Relationships
    material = relationship("Material", lazy="selectin")
    plant = relationship("Plant", lazy="selectin")

    def __repr__(self):
        return f"<MaterialProjection mat_id={self.material_id} plant_id={self.plant_id} date={self.date} bal={self.projected_balance}>"
