"""Material and Category models for manufacturing planning (replaces Product)."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Text,
    Boolean,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.models.base import TimeStampMixin


class MaterialCriticality(str, enum.Enum):
    """Criticality levels for manufacturing material."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ABCClassification(str, enum.Enum):
    """ABC inventory classification."""
    A = "A"
    B = "B"
    C = "C"


class ProcurementType(str, enum.Enum):
    """Procurement type: Make vs Buy."""
    MAKE = "MAKE"
    BUY = "BUY"


class Category(Base, TimeStampMixin):
    """Material category model."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Relationships
    parent = relationship(
        "Category", remote_side=[id], backref="subcategories"
    )
    materials = relationship(
        "Material", back_populates="category", lazy="select"
    )

    def __repr__(self):
        return f"<Category {self.name}>"


class Material(Base, TimeStampMixin):
    """Material specification model."""

    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    material_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Manufacturing Planning Attributes
    material_type = Column(String(50), nullable=False, default="RAW")  # RAW, COMPONENT, ASSEMBLY, FINISHED
    unit = Column(String(20), nullable=False, default="pcs")
    planner = Column(String(100), nullable=True)
    procurement_type = Column(SQLEnum(ProcurementType), nullable=False, default=ProcurementType.BUY)
    lead_time = Column(Integer, nullable=False, default=7)  # in days
    abc_classification = Column(SQLEnum(ABCClassification), nullable=False, default=ABCClassification.C)
    criticality = Column(SQLEnum(MaterialCriticality), nullable=False, default=MaterialCriticality.LOW)
    is_active = Column(Boolean, nullable=False, default=True)

    # Costing
    cost_price = Column(Float, nullable=False, default=0.0)
    selling_price = Column(Float, nullable=False, default=0.0)

    # Relationships
    category = relationship(
        "Category", back_populates="materials", lazy="selectin"
    )
    purchase_items = relationship(
        "PurchaseOrderItem", back_populates="material", lazy="select", cascade="all, delete-orphan"
    )
    locations = relationship(
        "Inventory", back_populates="material", lazy="select", cascade="all, delete-orphan"
    )
    ledger_entries = relationship(
        "StockLedger", back_populates="material", lazy="select", cascade="all, delete-orphan"
    )
    production_orders = relationship(
        "ProductionOrder", back_populates="material", lazy="select", cascade="all, delete-orphan"
    )
    bom = relationship(
        "BillOfMaterials", uselist=False, back_populates="material", lazy="select", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Material {self.material_code}: {self.name}>"
