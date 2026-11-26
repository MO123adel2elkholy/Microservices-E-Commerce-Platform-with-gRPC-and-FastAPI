"""Async gRPC client for communicating with the Product Service."""
import grpc

from product_service.generated import product_pb2, product_pb2_grpc
from order_service import config


class ProductGRPCClient:
    """Manages a persistent async gRPC channel to the Product Service."""

    def __init__(self):
        self._channel: grpc.aio.Channel | None = None
        self._stub: product_pb2_grpc.ProductServiceStub | None = None

    async def connect(self):
        """Open a persistent async gRPC channel."""
        target = f"{config.PRODUCT_SERVICE_GRPC_HOST}:{config.PRODUCT_SERVICE_GRPC_PORT}"
        self._channel = grpc.aio.insecure_channel(target)
        self._stub = product_pb2_grpc.ProductServiceStub(self._channel)
        print(f"[*] gRPC client connected to Product Service at {target}")

    async def close(self):
        """Gracefully close the gRPC channel."""
        if self._channel:
            await self._channel.close()
            print("[*] gRPC client channel closed")

    async def get_product(self, product_id: str) -> dict | None:
        """Fetch a single product from the Product Service."""
        try:
            response = await self._stub.GetProduct(
                product_pb2.ProductRequest(product_id=product_id), timeout=5.0
            )
            return {
                "product_id": response.product_id,
                "name": response.name,
                "description": response.description,
                "price": response.price,
                "stock": response.stock,
                "available": response.available,
            }
        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            raise

    async def validate_product(self, product_id: str, quantity: int) -> dict:
        """Validate product availability and get pricing via gRPC."""
        try:
            response = await self._stub.ValidateProduct(
                product_pb2.ProductValidationRequest(
                    product_id=product_id, quantity=quantity
                ),
                timeout=5.0,
            )
            return {
                "valid": response.valid,
                "message": response.message,
                "unit_price": response.unit_price,
                "total_price": response.total_price,
            }
        except grpc.aio.AioRpcError as e:
            raise RuntimeError(
                f"Product validation failed: {e.details()}"
            ) from e


# Singleton instance
product_client = ProductGRPCClient()
