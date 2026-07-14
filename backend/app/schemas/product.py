"""Backward compatibility schema module mapping Product to Material."""

from app.schemas.material import (
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    CategoryCreate,
    CategoryResponse,
)

ProductCreate = MaterialCreate
ProductUpdate = MaterialUpdate
ProductResponse = MaterialResponse
CategoryCreate = CategoryCreate
CategoryResponse = CategoryResponse
