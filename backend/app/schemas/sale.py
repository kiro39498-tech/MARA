"""Backward compatibility schema module mapping Sale to ProductionOrder."""

from app.schemas.production_order import (
    ProductionOrderCreate,
    ProductionOrderUpdate,
    ProductionOrderResponse,
)

SaleCreate = ProductionOrderCreate
SaleUpdate = ProductionOrderUpdate
SaleResponse = ProductionOrderResponse

class SaleItemCreate:
    pass

class SaleItemResponse:
    pass
