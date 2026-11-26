"""End-to-end integration tests for Product and Order microservices via gRPC."""
import asyncio
import pytest
import pytest_asyncio
import grpc
from httpx import AsyncClient, ASGITransport

from product_service.generated import product_pb2, product_pb2_grpc
from product_service.grpc_server import ProductServicer
from product_service import store as product_store
from order_service.main import app as order_app
from order_service.grpc_client import product_client
import order_service.config as order_config

TEST_GRPC_PORT = 50052


@pytest_asyncio.fixture
async def grpc_test_server():
    """Start gRPC server on a dedicated test port for integration testing."""
    await product_store.seed_initial_products()
    server = grpc.aio.server()
    product_pb2_grpc.add_ProductServiceServicer_to_server(ProductServicer(), server)
    listen_addr = f"127.0.0.1:{TEST_GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    await server.start()

    # Re-point order service gRPC client to the test port
    order_config.PRODUCT_SERVICE_GRPC_HOST = "127.0.0.1"
    order_config.PRODUCT_SERVICE_GRPC_PORT = TEST_GRPC_PORT

    yield server

    await server.stop(grace=0)


@pytest.mark.asyncio
async def test_direct_grpc_get_product(grpc_test_server):
    """Test direct gRPC communication with ProductServicer."""
    async with grpc.aio.insecure_channel(f"127.0.0.1:{TEST_GRPC_PORT}") as channel:
        stub = product_pb2_grpc.ProductServiceStub(channel)
        response = await stub.GetProduct(product_pb2.ProductRequest(product_id="prod-001"))
        assert response.product_id == "prod-001"
        assert response.name == "Wireless Headphones"
        assert response.price == 79.99
        assert response.available is True


@pytest.mark.asyncio
async def test_direct_grpc_product_not_found(grpc_test_server):
    """Test direct gRPC call returns NOT_FOUND for unknown product."""
    async with grpc.aio.insecure_channel(f"127.0.0.1:{TEST_GRPC_PORT}") as channel:
        stub = product_pb2_grpc.ProductServiceStub(channel)
        with pytest.raises(grpc.aio.AioRpcError) as exc_info:
            await stub.GetProduct(product_pb2.ProductRequest(product_id="prod-999"))
        assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND


@pytest.mark.asyncio
async def test_direct_grpc_validate_product(grpc_test_server):
    """Test direct gRPC stock validation."""
    async with grpc.aio.insecure_channel(f"127.0.0.1:{TEST_GRPC_PORT}") as channel:
        stub = product_pb2_grpc.ProductServiceStub(channel)

        # In stock
        valid_res = await stub.ValidateProduct(
            product_pb2.ProductValidationRequest(product_id="prod-001", quantity=2)
        )
        assert valid_res.valid is True
        assert valid_res.unit_price == 79.99
        assert valid_res.total_price == 159.98

        # Out of stock (prod-004 has stock=0)
        invalid_res = await stub.ValidateProduct(
            product_pb2.ProductValidationRequest(product_id="prod-004", quantity=1)
        )
        assert invalid_res.valid is False
        assert "Insufficient stock" in invalid_res.message


from unittest.mock import AsyncMock
from order_service.grpc_auth_client import user_client


@pytest.mark.asyncio
async def test_create_order_full_flow(grpc_test_server, monkeypatch):
    """
    Test Order Service REST API calling Product Service via gRPC
    to validate stock and prices when creating an order.
    """
    monkeypatch.setattr(
        user_client,
        "validate_token",
        AsyncMock(return_value={
            "valid": True,
            "message": "Token valid",
            "user_id": "usr-alice01",
            "email": "alice@example.com",
            "role": "customer",
            "full_name": "Alice Wonderland",
        }),
    )

    await product_client.connect()
    try:
        transport = ASGITransport(app=order_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            order_payload = {
                "items": [
                    {"product_id": "prod-001", "quantity": 2},
                    {"product_id": "prod-002", "quantity": 1},
                ],
            }
            headers = {"Authorization": "Bearer mock-token-123"}
            res = await ac.post("/orders", json=order_payload, headers=headers)
            assert res.status_code == 201
            data = res.json()
            assert data["customer_name"] == "Alice Wonderland"
            assert data["status"] == "confirmed"
            assert len(data["items"]) == 2
            # 79.99 * 2 + 129.99 * 1 = 159.98 + 129.99 = 289.97
            assert round(data["total_amount"], 2) == 289.97

            order_id = data["order_id"]

            # Verify order can be retrieved
            get_res = await ac.get(f"/orders/{order_id}", headers=headers)
            assert get_res.status_code == 200
            assert get_res.json()["order_id"] == order_id
    finally:
        await product_client.close()


@pytest.mark.asyncio
async def test_create_order_out_of_stock_rejected(grpc_test_server, monkeypatch):
    """Order creation rejected when product is out of stock."""
    monkeypatch.setattr(
        user_client,
        "validate_token",
        AsyncMock(return_value={
            "valid": True,
            "user_id": "usr-bob01",
            "email": "bob@example.com",
            "role": "customer",
            "full_name": "Bob Builder",
        }),
    )

    await product_client.connect()
    try:
        transport = ASGITransport(app=order_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            order_payload = {
                "items": [
                    {"product_id": "prod-004", "quantity": 1},
                ],
            }
            headers = {"Authorization": "Bearer mock-token-123"}
            res = await ac.post("/orders", json=order_payload, headers=headers)
            assert res.status_code == 400
            assert "Insufficient stock" in res.json()["detail"]
    finally:
        await product_client.close()


@pytest.mark.asyncio
async def test_create_order_invalid_product_rejected(grpc_test_server, monkeypatch):
    """Order creation rejected when product doesn't exist."""
    monkeypatch.setattr(
        user_client,
        "validate_token",
        AsyncMock(return_value={
            "valid": True,
            "user_id": "usr-charlie01",
            "email": "charlie@example.com",
            "role": "customer",
            "full_name": "Charlie",
        }),
    )

    await product_client.connect()
    try:
        transport = ASGITransport(app=order_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            order_payload = {
                "items": [
                    {"product_id": "non-existent-product", "quantity": 1},
                ],
            }
            headers = {"Authorization": "Bearer mock-token-123"}
            res = await ac.post("/orders", json=order_payload, headers=headers)
            assert res.status_code == 400
            assert "not found" in res.json()["detail"]
    finally:
        await product_client.close()
