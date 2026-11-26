import os
from pathlib import Path

HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8002"))

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_URL = f"sqlite+aiosqlite:///{(DATA_DIR / 'orders.db').resolve().as_posix()}"
DATABASE_URL = os.getenv("ORDER_DATABASE_URL", DEFAULT_SQLITE_URL)

# Product Service gRPC connection
PRODUCT_SERVICE_GRPC_HOST = os.getenv("PRODUCT_SERVICE_GRPC_HOST", "localhost")
PRODUCT_SERVICE_GRPC_PORT = int(os.getenv("PRODUCT_SERVICE_GRPC_PORT", "50051"))

# User Service gRPC connection
USER_SERVICE_GRPC_HOST = os.getenv("USER_SERVICE_GRPC_HOST", "localhost")
USER_SERVICE_GRPC_PORT = int(os.getenv("USER_SERVICE_GRPC_PORT", "50050"))
