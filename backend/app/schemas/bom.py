"""Bill Of Materials (BOM) schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.material import MaterialResponse


class BOMItemBase(BaseModel):
    component_id: int
    quantity: float = Field(1.0, gt=0.0)


class BOMItemCreate(BOMItemBase):
    pass


class BOMItemUpdate(BaseModel):
    component_id: Optional[int] = None
    quantity: Optional[float] = None


class BOMItemResponse(BOMItemBase):
    id: int
    bom_id: int
    created_at: datetime
    updated_at: datetime
    component: Optional[MaterialResponse] = None

    model_config = ConfigDict(from_attributes=True)


class BOMBase(BaseModel):
    material_id: int
    name: str = Field(..., max_length=100)
    version: str = "1.0"
    is_active: bool = True


class BOMCreate(BOMBase):
    items: list[BOMItemCreate] = []


class BOMUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None
    items: Optional[list[BOMItemCreate]] = None


class BOMResponse(BOMBase):
    id: int
    created_at: datetime
    updated_at: datetime
    material: Optional[MaterialResponse] = None
    items: list[BOMItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
