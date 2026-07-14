"""Backward compatibility module mapping ProductLocation to Inventory."""

from app.models.inventory import Inventory

ProductLocation = Inventory
