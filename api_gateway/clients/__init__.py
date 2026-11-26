"""Async gRPC client stubs used by the API Gateway."""
from api_gateway.clients.product_client import product_client
from api_gateway.clients.user_client import user_client

__all__ = ["product_client", "user_client"]
