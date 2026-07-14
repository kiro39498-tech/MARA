"""Backward compatibility schema module mapping ProductLocation to Inventory."""

from app.schemas.inventory import InventoryCreate, InventoryUpdate, InventoryResponse

ProductLocationCreate = InventoryCreate
ProductLocationUpdate = InventoryUpdate
ProductLocationResponse = InventoryResponse

class ProductStockByLocation:
    pass
