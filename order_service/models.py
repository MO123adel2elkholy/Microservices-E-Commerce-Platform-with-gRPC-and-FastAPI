"""Pydantic models for the Order Service REST API."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order lifecycle states."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class OrderItem(BaseModel):
    """A single item in an order request."""

    product_id: str
    quantity: int = Field(ge=1)


class CreateOrderRequest(BaseModel):
    """Request body for creating an order."""

    customer_name: Optional[str] = Field(
        None, description="Optional customer name; defaults to authenticated user's name"
    )
    items: list[OrderItem] = Field(min_length=1)


class OrderItemOut(BaseModel):
    """A single item in an order response (enriched with product details)."""

    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float


class OrderOut(BaseModel):
    """Order response model."""

    order_id: str
    customer_name: str
    items: list[OrderItemOut]
    total_amount: float
    status: OrderStatus


class OrderListOut(BaseModel):
    """List of orders response model."""

    orders: list[OrderOut]
    total: int
