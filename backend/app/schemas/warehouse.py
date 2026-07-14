"""Backward compatibility schema module mapping Warehouse to Plant."""

from app.schemas.plant import PlantCreate, PlantUpdate, PlantResponse

WarehouseCreate = PlantCreate
WarehouseUpdate = PlantUpdate
WarehouseResponse = PlantResponse
