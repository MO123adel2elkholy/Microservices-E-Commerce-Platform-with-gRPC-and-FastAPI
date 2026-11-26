import os
from pathlib import Path

HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8000"))

GRPC_HOST = os.getenv("GRPC_HOST", "0.0.0.0")
GRPC_PORT = int(os.getenv("GRPC_PORT", "50050"))

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_URL = f"sqlite+aiosqlite:///{(DATA_DIR / 'users.db').resolve().as_posix()}"
DATABASE_URL = os.getenv("USER_DATABASE_URL", DEFAULT_SQLITE_URL)

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "super-secret-jwt-key-change-in-production-12345"
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
