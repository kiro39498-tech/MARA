"""Supplier model."""

from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimeStampMixin


class Supplier(Base, TimeStampMixin):
    """Supplier model for vendor management."""

    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)

    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)

    # Additional Info
    contact_person = Column(String(255), nullable=True)
    tax_id = Column(String(50), nullable=True)
    payment_terms = Column(
        String(100), nullable=True
    )  # e.g., "Net 30", "Net 60"
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    purchase_orders = relationship(
        "PurchaseOrder", back_populates="supplier", lazy="select"
    )

    def __repr__(self):
        return f"<Supplier {self.code}: {self.name}>"
