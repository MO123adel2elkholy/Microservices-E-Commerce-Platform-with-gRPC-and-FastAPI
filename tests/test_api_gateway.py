"""Integration tests for API Gateway orchestration and unified routes."""
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from api_gateway.clients import product_client, user_client
from api_gateway.main import app
from api_gateway.models import CheckoutItem
from api_gateway.orchestrator import checkout


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_gateway_health_check(monkeypatch):
    """Gateway health endpoint returns ok without requiring live gRPC peers."""
    monkeypatch.setattr(user_client, "connect", AsyncMock())
    monkeypatch.setattr(product_client, "connect", AsyncMock())
    monkeypatch.setattr(user_client, "close", AsyncMock())
    monkeypatch.setattr(product_client, "close", AsyncMock())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "api-gateway"


@pytest.mark.asyncio
async def test_checkout_requires_bearer_token(monkeypatch):
    """Checkout without Authorization returns 401."""
    monkeypatch.setattr(user_client, "connect", AsyncMock())
    monkeypatch.setattr(product_client, "connect", AsyncMock())
    monkeypatch.setattr(user_client, "close", AsyncMock())
    monkeypatch.setattr(product_client, "close", AsyncMock())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/checkout",
            json={"items": [{"product_id": "prod-001", "quantity": 1}]},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_checkout_orchestration_success(monkeypatch):
    """Checkout validates token, checks stock, then places the order."""
    monkeypatch.setattr(user_client, "connect", AsyncMock())
    monkeypatch.setattr(product_client, "connect", AsyncMock())
    monkeypatch.setattr(user_client, "close", AsyncMock())
    monkeypatch.setattr(product_client, "close", AsyncMock())
    monkeypatch.setattr(
        user_client,
        "validate_token",
        AsyncMock(
            return_value={
                "valid": True,
                "message": "Token is valid",
                "user_id": "usr-alice01",
                "email": "alice@example.com",
                "role": "customer",
                "full_name": "Alice Wonderland",
            }
        ),
    )
    monkeypatch.setattr(
        product_client,
        "validate_product",
        AsyncMock(
            return_value={
                "valid": True,
                "message": "Product available",
                "unit_price": 79.99,
                "total_price": 79.99,
            }
        ),
    )

    order_body = {
        "order_id": "ord-test01",
        "customer_name": "Alice Wonderland",
        "items": [
            {
                "product_id": "prod-001",
                "product_name": "Wireless Headphones",
                "quantity": 1,
                "unit_price": 79.99,
                "total_price": 79.99,
            }
        ],
        "total_amount": 79.99,
        "status": "confirmed",
    }

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = order_body

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=mock_response)
    mock_http.aclose = AsyncMock()
    mock_http.request = AsyncMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Replace the lifespan HTTP client after startup.
        app.state.http = mock_http
        response = await ac.post(
            "/api/v1/checkout",
            json={"items": [{"product_id": "prod-001", "quantity": 1}]},
            headers={"Authorization": "Bearer mock-token"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == "ord-test01"
    assert data["status"] == "confirmed"
    user_client.validate_token.assert_awaited()
    product_client.validate_product.assert_awaited()
    mock_http.post.assert_awaited()


@pytest.mark.asyncio
async def test_checkout_rejects_out_of_stock(monkeypatch):
    """Orchestrator stops checkout when Product Service reports insufficient stock."""
    monkeypatch.setattr(
        user_client,
        "validate_token",
        AsyncMock(return_value={"valid": True, "message": "ok"}),
    )
    monkeypatch.setattr(
        product_client,
        "validate_product",
        AsyncMock(
            return_value={
                "valid": False,
                "message": "Insufficient stock (available: 0)",
                "unit_price": 99.99,
                "total_price": 0.0,
            }
        ),
    )

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    with pytest.raises(Exception) as exc_info:
        await checkout(
            token="mock-token",
            items=[CheckoutItem(product_id="prod-004", quantity=1)],
            http_client=mock_http,
        )
    assert exc_info.value.status_code == 400
    assert "Insufficient stock" in exc_info.value.detail
    mock_http.post.assert_not_called()
