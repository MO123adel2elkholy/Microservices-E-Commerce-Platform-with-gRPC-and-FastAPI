"""Database-backed order persistence repository."""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from order_service.database import AsyncSessionLocal, init_db
from order_service.models_db import OrderItemModel, OrderModel


async def init_store():
    """Ensure order tables exist."""
    await init_db()


async def create_order(
    customer_name: str, items: list[dict], total_amount: float, user_id: str
) -> dict:
    """Create and persist a new order. Returns the order dict."""
    order_id = f"ord-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as session:
        order = OrderModel(
            order_id=order_id,
            user_id=user_id,
            customer_name=customer_name,
            total_amount=total_amount,
            status="confirmed",
            items=[
                OrderItemModel(
                    product_id=item["product_id"],
                    product_name=item["product_name"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total_price=item["total_price"],
                )
                for item in items
            ],
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order.to_dict()


async def get_order(order_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    """Get a single order by ID."""
    async with AsyncSessionLocal() as session:
        query = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.order_id == order_id)
        )
        if user_id is not None:
            query = query.where(OrderModel.user_id == user_id)
        result = await session.execute(query)
        order = result.scalar_one_or_none()
        return order.to_dict() if order else None


async def list_orders(user_id: Optional[str] = None) -> list[dict]:
    """List orders, optionally restricted to their owner."""
    async with AsyncSessionLocal() as session:
        query = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .order_by(OrderModel.created_at.desc())
        )
        if user_id is not None:
            query = query.where(OrderModel.user_id == user_id)
        result = await session.execute(query)
        orders = result.scalars().all()
        return [order.to_dict() for order in orders]
