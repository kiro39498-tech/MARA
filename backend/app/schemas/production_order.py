"""Production Order schemas representing demand."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.material import MaterialResponse
from app.schemas.plant import PlantResponse


class ProductionOrderBase(BaseModel):
    order_number: str = Field(..., max_length=50)
    material_id: int
    plant_id: int
    quantity: int = Field(1, ge=1)
    start_date: date
    required_date: date
    status: str = "PLANNED"  # DRAFT, PLANNED, IN_PROGRESS, COMPLETED, CANCELLED
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL


class ProductionOrderCreate(ProductionOrderBase):
    pass


class ProductionOrderUpdate(BaseModel):
    material_id: Optional[int] = None
    plant_id: Optional[int] = None
    quantity: Optional[int] = None
    start_date: Optional[date] = None
    required_date: Optional[date] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class ProductionOrderResponse(ProductionOrderBase):
    id: int
    created_at: datetime
    updated_at: datetime
    material: Optional[MaterialResponse] = None
    plant: Optional[PlantResponse] = None

    model_config = ConfigDict(from_attributes=True)
