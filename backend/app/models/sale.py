"""Backward compatibility module mapping Sale to ProductionOrder."""

from app.models.production_order import ProductionOrder
import enum

class SaleStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

Sale = ProductionOrder

# Dummy SaleItem class for imports
class SaleItem:
    pass
