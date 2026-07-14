"""Production Order model representing demand."""

from sqlalchemy import Column, Integer, ForeignKey, String, Date
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimeStampMixin


class ProductionOrder(Base, TimeStampMixin):
    """
    Production Order represents demand for a material to be manufactured at a plant.
    """

    __tablename__ = "production_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
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
    quantity = Column(Integer, nullable=False, default=1)
    start_date = Column(Date, nullable=False)
    required_date = Column(Date, nullable=False)
    status = Column(String(30), nullable=False, default="PLANNED")  # DRAFT, PLANNED, IN_PROGRESS, COMPLETED, CANCELLED
    priority = Column(String(20), nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL

    # Relationships
    material = relationship("Material", back_populates="production_orders", lazy="selectin")
    plant = relationship("Plant", back_populates="production_orders", lazy="selectin")

    def __repr__(self):
        return f"<ProductionOrder {self.order_number} material_id={self.material_id} qty={self.quantity}>"
