"""Port settings and upstream targets for the API Gateway."""
import os

HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8080"))

USER_SERVICE_GRPC_HOST = os.getenv("USER_SERVICE_GRPC_HOST", "localhost")
USER_SERVICE_GRPC_PORT = int(os.getenv("USER_SERVICE_GRPC_PORT", "50050"))

PRODUCT_SERVICE_GRPC_HOST = os.getenv("PRODUCT_SERVICE_GRPC_HOST", "localhost")
PRODUCT_SERVICE_GRPC_PORT = int(os.getenv("PRODUCT_SERVICE_GRPC_PORT", "50051"))

USER_SERVICE_HTTP_URL = os.getenv("USER_SERVICE_HTTP_URL", "http://localhost:8000")
ORDER_SERVICE_HTTP_URL = os.getenv("ORDER_SERVICE_HTTP_URL", "http://localhost:8002")
