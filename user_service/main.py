"""User Service — FastAPI HTTP + gRPC Server for Authentication & Authorization."""
from contextlib import asynccontextmanager
import grpc
import uvicorn
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from user_service.config import GRPC_HOST, GRPC_PORT, HTTP_HOST, HTTP_PORT
from user_service.generated import user_pb2_grpc
from user_service.grpc_server import UserServicer
from user_service.models import (
    TokenResponse,
    UserLoginRequest,
    UserOut,
    UserRegisterRequest,
)
from user_service.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from user_service import store


# ── gRPC Server Lifespan ─────────────────────────────────


async def start_grpc_server() -> grpc.aio.Server:
    """Start the asynchronous gRPC server."""
    server = grpc.aio.server()
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServicer(), server)
    listen_addr = f"{GRPC_HOST}:{GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    await server.start()
    print(f"[*] User gRPC server listening on {listen_addr}")
    return server


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the database initialization and async gRPC server alongside FastAPI."""
    await store.seed_initial_users()
    grpc_server = await start_grpc_server()
    yield
    await grpc_server.stop(grace=0)
    print("[*] User gRPC server stopped")


# ── FastAPI App ──────────────────────────────────────────

app = FastAPI(
    title="User Service",
    description="Identity, Authentication (JWT), and Authorization microservice with gRPC backend",
    version="1.0.0",
    lifespan=lifespan,
)

security_scheme = HTTPBearer(auto_error=False)


# ── Dependencies ─────────────────────────────────────────


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
) -> dict:
    """Validate Bearer JWT and return user record."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    claims = decode_access_token(credentials.credentials)
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
    user_id = claims.get("sub")
    user = await store.get_user_by_id(user_id)
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def require_admin(current_user: dict = Security(get_current_user)) -> dict:
    """Restrict administrative endpoints to active administrators."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return current_user


# ── HTTP Routes ──────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Service health probe."""
    return {"status": "healthy", "service": "user-service"}


@app.post(
    "/auth/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register(request: UserRegisterRequest):
    """Register a new user account."""
    try:
        user = await store.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            role=request.role,
        )
        return UserOut(
            user_id=user["user_id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            is_active=user["is_active"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.post("/auth/login", response_model=TokenResponse)
async def login(request: UserLoginRequest):
    """Authenticate with email and password to receive a JWT access token."""
    user = await store.get_user_by_email(request.email)
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Issue JWT token
    token = create_access_token(
        data={
            "sub": user["user_id"],
            "email": user["email"],
            "role": user["role"],
            "full_name": user["full_name"],
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user["user_id"],
        email=user["email"],
        role=user["role"],
        full_name=user["full_name"],
    )


@app.get("/auth/me", response_model=UserOut)
async def get_me(current_user: dict = Security(get_current_user)):
    """Retrieve the currently authenticated user's profile."""
    return UserOut(
        user_id=current_user["user_id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        is_active=current_user["is_active"],
    )


@app.get("/users", response_model=list[UserOut])
async def list_all_users(current_user: dict = Security(require_admin)):
    """List registered users for administrators."""
    users = await store.list_users()
    return [
        UserOut(
            user_id=u["user_id"],
            email=u["email"],
            full_name=u["full_name"],
            role=u["role"],
            is_active=u["is_active"],
        )
        for u in users
    ]


# ── Entrypoint ───────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "user_service.main:app",
        host=HTTP_HOST,
        port=HTTP_PORT,
        reload=True,
    )
