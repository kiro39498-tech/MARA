"""Plant model for tracking inventory across manufacturing plants (replaces Warehouse)."""

from sqlalchemy import Column, Integer, String, Text, Boolean, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimeStampMixin


class Plant(Base, TimeStampMixin):
    """Plant model for tracking inventory across multiple manufacturing sites."""

    __tablename__ = "plants"
    __table_args__ = (
        Index("ix_plants_name", "name"),
        Index("ix_plants_city", "city"),
        Index("ix_plants_is_active", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    contact_person = Column(String(255), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    stock_locations = relationship(
        "Inventory",
        back_populates="plant",
        lazy="select",
        cascade="all, delete-orphan",
    )
    stock_ledger_entries = relationship(
        "StockLedger", back_populates="plant", lazy="select"
    )
    purchase_orders = relationship(
        "PurchaseOrder", back_populates="plant", lazy="select"
    )
    production_orders = relationship(
        "ProductionOrder", back_populates="plant", lazy="select"
    )

    def __repr__(self):
        return f"<Plant {self.code}: {self.name}>"
