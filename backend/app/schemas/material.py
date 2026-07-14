"""Material schemas for validation and API serialization."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.material import MaterialCriticality, ABCClassification, ProcurementType


class MaterialBase(BaseModel):
    material_code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    material_type: str = "RAW"
    unit: str = "pcs"
    planner: Optional[str] = None
    procurement_type: ProcurementType = ProcurementType.BUY
    lead_time: int = Field(7, ge=0)
    abc_classification: ABCClassification = ABCClassification.C
    criticality: MaterialCriticality = MaterialCriticality.LOW
    is_active: bool = True
    cost_price: float = Field(0.0, ge=0.0)
    selling_price: float = Field(0.0, ge=0.0)


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    material_code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    material_type: Optional[str] = None
    unit: Optional[str] = None
    planner: Optional[str] = None
    procurement_type: Optional[ProcurementType] = None
    lead_time: Optional[int] = None
    abc_classification: Optional[ABCClassification] = None
    criticality: Optional[MaterialCriticality] = None
    is_active: Optional[bool] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None


class CategorySimple(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryResponse(CategoryCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaterialResponse(MaterialBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[CategorySimple] = None

    model_config = ConfigDict(from_attributes=True)
