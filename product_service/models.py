"""Pydantic models for the Product Service REST API."""
from pydantic import BaseModel


class ProductOut(BaseModel):
    """Product response model."""

    product_id: str
    name: str
    description: str
    price: float
    stock: int
    available: bool


class ProductListOut(BaseModel):
    """Paginated product list response model."""

    products: list[ProductOut]
    total: int
    page: int
    page_size: int
