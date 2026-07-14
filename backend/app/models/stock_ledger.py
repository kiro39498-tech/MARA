"""StockLedger model - append-only inventory journal."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class StockTransactionType(str, enum.Enum):
    """Stock transaction type enumeration."""

    IN = "in"  # Stock increase (purchase receive)
    OUT = "out"  # Stock decrease (production consumption/sale complete)
    ADJUST = "adjust"  # Manual adjustment (inventory count correction)
    TRANSFER = "transfer"  # Transfer between plants


class StockLedger(Base):
    """
    Append-only inventory journal.
    Every stock change MUST create a ledger entry.
    This is the source of truth for inventory history.
    """

    __tablename__ = "stock_ledger"

    id = Column(Integer, primary_key=True, index=True)

    # What changed
    material_id = Column(
        Integer, ForeignKey("materials.id"), nullable=False, index=True
    )
    plant_id = Column(
        Integer, ForeignKey("plants.id"), nullable=False, index=True
    )

    # Transaction type
    type = Column(SQLEnum(StockTransactionType), nullable=False, index=True)

    # Quantity change
    qty_change = Column(
        Integer, nullable=False
    )  # Positive for IN, negative for OUT
    qty_before = Column(Integer, nullable=False)
    qty_after = Column(Integer, nullable=False)

    # Reference (what caused this change)
    reference_type = Column(
        String(50), nullable=True, index=True
    )  # e.g., "purchase", "production", "adjustment"
    reference_id = Column(
        Integer, nullable=True, index=True
    )  # ID of the purchase_order/production_order/etc

    # Metadata
    note = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    material = relationship(
        "Material", back_populates="ledger_entries", lazy="selectin"
    )
    plant = relationship(
        "Plant", back_populates="stock_ledger_entries", lazy="selectin"
    )
    user = relationship("User", lazy="selectin")

    def __repr__(self):
        return (
            f"<StockLedger {self.type.value}: material_id={self.material_id}, "
            f"qty={self.qty_change:+d}>"
        )
