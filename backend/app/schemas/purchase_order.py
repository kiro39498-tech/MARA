"""Purchase Order schemas representing supply."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.material import MaterialResponse
from app.schemas.plant import PlantResponse
from app.schemas.supplier import SupplierResponse


class PurchaseOrderItemBase(BaseModel):
    material_id: int
    quantity: int = Field(1, ge=1)
    received_quantity: int = Field(0, ge=0)
    unit_price: float = Field(0.0, ge=0.0)
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None


class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass


class PurchaseOrderItemUpdate(BaseModel):
    material_id: Optional[int] = None
    quantity: Optional[int] = None
    received_quantity: Optional[int] = None
    unit_price: Optional[float] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None


class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    id: int
    purchase_order_id: int
    total_price: float
    created_at: datetime
    updated_at: datetime
    material: Optional[MaterialResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseModel):
    po_number: str = Field(..., max_length=50)
    supplier_id: int
    plant_id: int
    status: str = "DRAFT"
    order_date: date
    expected_receipt_date: date
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    items: list[PurchaseOrderItemCreate] = []


class PurchaseOrderUpdate(BaseModel):
    supplier_id: Optional[int] = None
    plant_id: Optional[int] = None
    status: Optional[str] = None
    order_date: Optional[date] = None
    expected_receipt_date: Optional[date] = None
    notes: Optional[str] = None
    items: Optional[list[PurchaseOrderItemCreate]] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    total_amount: float
    created_at: datetime
    updated_at: datetime
    supplier: Optional[SupplierResponse] = None
    plant: Optional[PlantResponse] = None
    items: list[PurchaseOrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
