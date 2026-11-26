"""Tests for the Order Service REST API."""
import pytest
from httpx import AsyncClient, ASGITransport

from order_service.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Order service health endpoint returns ok."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "order-service"


@pytest.mark.asyncio
async def test_create_order_unauthorized():
    """Creating an order without a Bearer token returns 401 Unauthorized."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/orders",
            json={"items": [{"product_id": "prod-001", "quantity": 1}]},
        )
    assert response.status_code == 401
    assert "Missing Authorization" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_orders_unauthorized():
    """Listing orders without authentication returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/orders")
    assert response.status_code == 401
