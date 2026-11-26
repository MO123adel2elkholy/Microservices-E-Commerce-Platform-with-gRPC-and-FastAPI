"""Async gRPC client for ProductService."""
import grpc

from api_gateway import config
from product_service.generated import product_pb2, product_pb2_grpc


class ProductGRPCClient:
    """Long-lived async channel to Product Service."""

    def __init__(self):
        self._channel: grpc.aio.Channel | None = None
        self._stub: product_pb2_grpc.ProductServiceStub | None = None

    async def connect(self):
        """Open a persistent async gRPC channel."""
        target = f"{config.PRODUCT_SERVICE_GRPC_HOST}:{config.PRODUCT_SERVICE_GRPC_PORT}"
        self._channel = grpc.aio.insecure_channel(target)
        self._stub = product_pb2_grpc.ProductServiceStub(self._channel)
        print(f"[*] Gateway gRPC client connected to Product Service at {target}")

    async def close(self):
        """Close the gRPC channel."""
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None

    async def get_product(self, product_id: str) -> dict | None:
        """Fetch a catalog item by ID."""
        try:
            response = await self._stub.GetProduct(
                product_pb2.ProductRequest(product_id=product_id)
            )
            return _product_to_dict(response)
        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            raise

    async def list_products(self, page: int = 1, page_size: int = 10) -> dict:
        """List catalog items with pagination."""
        response = await self._stub.ListProducts(
            product_pb2.ProductListRequest(page=page, page_size=page_size)
        )
        return {
            "products": [_product_to_dict(p) for p in response.products],
            "total": response.total,
            "page": page,
            "page_size": page_size,
        }

    async def validate_product(self, product_id: str, quantity: int) -> dict:
        """Validate stock and pricing for checkout."""
        try:
            response = await self._stub.ValidateProduct(
                product_pb2.ProductValidationRequest(
                    product_id=product_id,
                    quantity=quantity,
                )
            )
            return {
                "valid": response.valid,
                "message": response.message,
                "unit_price": response.unit_price,
                "total_price": response.total_price,
            }
        except grpc.aio.AioRpcError as e:
            raise RuntimeError(f"Product validation failed: {e.details()}") from e


def _product_to_dict(response) -> dict:
    return {
        "product_id": response.product_id,
        "name": response.name,
        "description": response.description,
        "price": response.price,
        "stock": response.stock,
        "available": response.available,
    }


product_client = ProductGRPCClient()
