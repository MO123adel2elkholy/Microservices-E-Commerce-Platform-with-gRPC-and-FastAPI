"""Database-backed catalog repository with stock validation."""
from typing import Optional

from sqlalchemy import func, select

from product_service.database import AsyncSessionLocal, init_db
from product_service.models_db import ProductModel

SEED_PRODUCTS = [
    {
        "product_id": "prod-001",
        "name": "Wireless Headphones",
        "description": "Noise-cancelling Bluetooth headphones",
        "price": 79.99,
        "stock": 150,
    },
    {
        "product_id": "prod-002",
        "name": "Mechanical Keyboard",
        "description": "RGB mechanical keyboard with Cherry MX switches",
        "price": 129.99,
        "stock": 75,
    },
    {
        "product_id": "prod-003",
        "name": "USB-C Hub",
        "description": "7-in-1 USB-C hub with HDMI and Ethernet",
        "price": 49.99,
        "stock": 200,
    },
    {
        "product_id": "prod-004",
        "name": "Webcam 4K",
        "description": "4K webcam with autofocus and built-in mic",
        "price": 99.99,
        "stock": 0,
    },
]


async def seed_initial_products():
    """Create schema and seed the default catalog when empty."""
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ProductModel).limit(1))
        if result.scalar_one_or_none():
            return

        session.add_all([ProductModel(**item) for item in SEED_PRODUCTS])
        await session.commit()


async def get_product(product_id: str) -> Optional[dict]:
    """Get a single product by ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ProductModel).where(ProductModel.product_id == product_id)
        )
        product = result.scalar_one_or_none()
        return product.to_dict() if product else None


async def list_products(page: int = 1, page_size: int = 10) -> tuple[list[dict], int]:
    """List products with pagination. Returns (products, total_count)."""
    async with AsyncSessionLocal() as session:
        total_result = await session.execute(select(func.count()).select_from(ProductModel))
        total = int(total_result.scalar_one())
        start = (page - 1) * page_size
        result = await session.execute(
            select(ProductModel)
            .order_by(ProductModel.product_id)
            .offset(start)
            .limit(page_size)
        )
        products = result.scalars().all()
        return [p.to_dict() for p in products], total


async def validate_product(product_id: str, quantity: int) -> tuple[bool, str, float]:
    """
    Validate product availability and return pricing.
    Returns (valid, message, unit_price).
    """
    product = await get_product(product_id)
    if not product:
        return False, f"Product '{product_id}' not found", 0.0
    if product["stock"] < quantity:
        return (
            False,
            f"Insufficient stock (available: {product['stock']})",
            product["price"],
        )
    return True, "Product available", product["price"]
