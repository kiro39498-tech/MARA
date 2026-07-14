"""Material Risk model."""

from sqlalchemy import Column, Integer, ForeignKey, Float, Date, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimeStampMixin


class MaterialRisk(Base, TimeStampMixin):
    """
    Stores risk score details and shortage analysis for a material at a specific plant.
    """

    __tablename__ = "material_risks"

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

    # Risk Metrics (0.0 to 100.0)
    risk_score = Column(Float, nullable=False, default=0.0)
    urgency = Column(Float, nullable=False, default=0.0)
    material_criticality = Column(Float, nullable=False, default=0.0)
    production_impact = Column(Float, nullable=False, default=0.0)
    supplier_delay = Column(Float, nullable=False, default=0.0)
    safety_stock_violation = Column(Float, nullable=False, default=0.0)
    late_po = Column(Float, nullable=False, default=0.0)

    reason = Column(Text, nullable=True)

    # Shortage Stats
    first_shortage_date = Column(Date, nullable=True)
    shortage_quantity = Column(Integer, nullable=True)
    recovery_date = Column(Date, nullable=True)
    days_of_coverage = Column(Integer, nullable=True)

    # Relationships
    material = relationship("Material", lazy="selectin")
    plant = relationship("Plant", lazy="selectin")

    def __repr__(self):
        return f"<MaterialRisk mat_id={self.material_id} plant_id={self.plant_id} score={self.risk_score}>"
