"""Supplier Performance model."""

from sqlalchemy import Column, Integer, ForeignKey, Float, Date
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimeStampMixin


class SupplierPerformance(Base, TimeStampMixin):
    """
    Stores metrics on vendor reliability, including delivery on-time rate, lead time variance, and quality rating.
    """

    __tablename__ = "supplier_performances"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evaluation_date = Column(Date, nullable=False)
    on_time_delivery_rate = Column(Float, nullable=False, default=1.0)  # 0.0 to 1.0
    quality_rating = Column(Float, nullable=False, default=100.0)        # 0.0 to 100.0
    lead_time_variance = Column(Float, nullable=False, default=0.0)    # standard deviation in days
    total_orders = Column(Integer, nullable=False, default=0)
    late_orders = Column(Integer, nullable=False, default=0)

    # Relationships
    supplier = relationship("Supplier", lazy="selectin")

    def __repr__(self):
        return f"<SupplierPerformance supplier_id={self.supplier_id} rating={self.quality_rating}>"
