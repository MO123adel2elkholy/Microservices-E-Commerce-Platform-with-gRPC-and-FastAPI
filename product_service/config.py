import os
from pathlib import Path

GRPC_HOST = os.getenv("GRPC_HOST", "0.0.0.0")
GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))
HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8001"))

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_URL = f"sqlite+aiosqlite:///{(DATA_DIR / 'products.db').resolve().as_posix()}"
DATABASE_URL = os.getenv("PRODUCT_DATABASE_URL", DEFAULT_SQLITE_URL)
