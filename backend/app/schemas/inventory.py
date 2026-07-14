"""Inventory schemas for validation and API serialization."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.material import MaterialResponse
from app.schemas.plant import PlantResponse


class InventoryBase(BaseModel):
    material_id: int
    plant_id: int
    on_hand: int = Field(0, ge=0)
    reserved: int = Field(0, ge=0)
    blocked: int = Field(0, ge=0)
    quality_hold: int = Field(0, ge=0)
    in_transit: int = Field(0, ge=0)
    safety_stock: int = Field(0, ge=0)
    buffer_stock: int = Field(0, ge=0)
    reorder_point: int = Field(0, ge=0)


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    on_hand: Optional[int] = None
    reserved: Optional[int] = None
    blocked: Optional[int] = None
    quality_hold: Optional[int] = None
    in_transit: Optional[int] = None
    safety_stock: Optional[int] = None
    buffer_stock: Optional[int] = None
    reorder_point: Optional[int] = None


class InventoryResponse(InventoryBase):
    id: int
    usable_inventory: int
    created_at: datetime
    updated_at: datetime
    material: Optional[MaterialResponse] = None
    plant: Optional[PlantResponse] = None

    model_config = ConfigDict(from_attributes=True)
