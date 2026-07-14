"""Backward compatibility module mapping Purchase to PurchaseOrder."""

from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
import enum

class PurchaseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"

Purchase = PurchaseOrder
PurchaseItem = PurchaseOrderItem
