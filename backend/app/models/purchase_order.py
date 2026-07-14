"""Purchase Order model representing supply."""

from sqlalchemy import Column, Integer, ForeignKey, String, Date, Float, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimeStampMixin


class PurchaseOrder(Base, TimeStampMixin):
    """
    Purchase Order representing supply incoming from vendors.
    """

    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, index=True, nullable=False)
    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plant_id = Column(
        Integer,
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(30), nullable=False, default="DRAFT")  # DRAFT, SENT, PARTIALLY_RECEIVED, RECEIVED, CANCELLED
    total_amount = Column(Float, nullable=False, default=0.0)
    order_date = Column(Date, nullable=False)
    expected_receipt_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders", lazy="selectin")
    plant = relationship("Plant", back_populates="purchase_orders", lazy="selectin")
    items = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<PurchaseOrder {self.po_number} supplier_id={self.supplier_id} status={self.status}>"


class PurchaseOrderItem(Base, TimeStampMixin):
    """
    Items inside a Purchase Order.
    """

    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(
        Integer,
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    material_id = Column(
        Integer,
        ForeignKey("materials.id"),
        nullable=False,
        index=True,
    )
    quantity = Column(Integer, nullable=False, default=1)
    received_quantity = Column(Integer, nullable=False, default=0)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)
    batch_number = Column(String(100), nullable=True)
    expiry_date = Column(Date, nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items", lazy="select")
    material = relationship("Material", back_populates="purchase_items", lazy="selectin")

    def __repr__(self):
        return (
            f"<PurchaseOrderItem po_id={self.purchase_order_id} "
            f"material_id={self.material_id} quantity={self.quantity}>"
        )
