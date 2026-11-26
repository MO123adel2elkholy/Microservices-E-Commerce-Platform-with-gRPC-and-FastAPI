"""Pydantic models for the API Gateway REST surface."""
from typing import Optional

from pydantic import BaseModel, Field


class CheckoutItem(BaseModel):
    """A line item in a composite checkout request."""

    product_id: str
    quantity: int = Field(ge=1)


class CheckoutRequest(BaseModel):
    """Composite checkout payload."""

    customer_name: Optional[str] = None
    items: list[CheckoutItem] = Field(min_length=1)
