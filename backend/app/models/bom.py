"""Bill Of Materials (BOM) and BOM Items models."""

from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimeStampMixin


class BillOfMaterials(Base, TimeStampMixin):
    """
    Header table for Bill Of Materials.
    Defines the components needed to manufacture an assembly material.
    """

    __tablename__ = "boms"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(
        Integer,
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    name = Column(String(100), nullable=False)
    version = Column(String(10), nullable=False, default="1.0")
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    material = relationship("Material", back_populates="bom", lazy="selectin")
    items = relationship(
        "BOMItem",
        back_populates="bom",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<BOM assembly_id={self.material_id} name={self.name}>"


class BOMItem(Base, TimeStampMixin):
    """
    Line items for a Bill Of Materials, specifying component quantities.
    """

    __tablename__ = "bom_items"

    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(
        Integer,
        ForeignKey("boms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    component_id = Column(
        Integer,
        ForeignKey("materials.id"),
        nullable=False,
        index=True,
    )
    quantity = Column(Float, nullable=False, default=1.0)  # Qty required per 1 unit of assembly

    # Relationships
    bom = relationship("BillOfMaterials", back_populates="items", lazy="select")
    component = relationship("Material", lazy="selectin")

    def __repr__(self):
        return f"<BOMItem bom_id={self.bom_id} component_id={self.component_id} qty={self.quantity}>"
