"""Backward compatibility schema module mapping Purchase to PurchaseOrder."""

from datetime import date
from pydantic import BaseModel
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderItemCreate,
    PurchaseOrderItemResponse,
)

PurchaseCreate = PurchaseOrderCreate
PurchaseUpdate = PurchaseOrderUpdate
PurchaseResponse = PurchaseOrderResponse
PurchaseItemCreate = PurchaseOrderItemCreate
PurchaseItemResponse = PurchaseOrderItemResponse

class ReceivePurchaseRequest(BaseModel):
    """Schema for receiving a purchase order."""

    items: list[dict]  # [{"purchase_item_id": int, "received_quantity": int}]
    received_date: date
