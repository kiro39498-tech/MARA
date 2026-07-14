"""Backward compatibility module mapping Product to Material."""

from app.models.material import Material, Category
import enum

class StockStatus(str, enum.Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"

Product = Material
Category = Category
