"""API Gateway — unified REST entrypoint, reverse proxy, and checkout orchestration."""
from contextlib import asynccontextmanager
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, Security, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api_gateway.clients import product_client, user_client
from api_gateway.config import (
    HTTP_HOST,
    HTTP_PORT,
    ORDER_SERVICE_HTTP_URL,
    USER_SERVICE_HTTP_URL,
)
from api_gateway.models import CheckoutRequest
from api_gateway.orchestrator import checkout
from order_service.models import CreateOrderRequest, OrderListOut, OrderOut
from user_service.models import TokenResponse, UserLoginRequest, UserOut, UserRegisterRequest

security_scheme = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open gRPC channels and an HTTP client for downstream REST calls."""
    await user_client.connect()
    await product_client.connect()
    app.state.http = httpx.AsyncClient(timeout=30.0)
    yield
    await app.state.http.aclose()
    await product_client.close()
    await user_client.close()


app = FastAPI(
    title="API Gateway",
    description="Unified OpenAPI surface, reverse proxy, and composite checkout orchestrator",
    version="1.0.0",
    lifespan=lifespan,
)


def _http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


async def _proxy(
    request: Request,
    upstream_url: str,
    extra_headers: Optional[dict] = None,
) -> JSONResponse:
    """Forward a request to a downstream HTTP service."""
    headers = {}
    auth = request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
    if extra_headers:
        headers.update(extra_headers)

    body = None
    if request.method in {"POST", "PUT", "PATCH"}:
        body = await request.body()
        content_type = request.headers.get("content-type")
        if content_type:
            headers["Content-Type"] = content_type

    client = _http_client(request)
    try:
        response = await client.request(
            request.method,
            upstream_url,
            params=request.query_params,
            content=body,
            headers=headers,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Upstream service unavailable at {upstream_url}: "
                f"{type(exc).__name__}: {exc!r}"
            ),
        ) from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text}
    return JSONResponse(content=payload, status_code=response.status_code)


# ── Health ───────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Gateway health probe."""
    return {"status": "healthy", "service": "api-gateway"}


# ── Auth reverse proxy → User Service HTTP ───────────────


@app.post("/api/v1/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def proxy_register(payload: UserRegisterRequest, request: Request):
    """Register a user through the User Service."""
    return await _proxy(request, f"{USER_SERVICE_HTTP_URL}/auth/register")


@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def proxy_login(payload: UserLoginRequest, request: Request):
    """Authenticate through the User Service and receive a JWT."""
    return await _proxy(request, f"{USER_SERVICE_HTTP_URL}/auth/login")


@app.get("/api/v1/auth/me", response_model=UserOut)
async def proxy_current_user(request: Request):
    """Get the current user's profile through the User Service."""
    return await _proxy(request, f"{USER_SERVICE_HTTP_URL}/auth/me")


# ── Catalog via Product Service gRPC ─────────────────────


@app.get("/api/v1/catalog")
async def list_catalog(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """List products through the Product Service gRPC catalog."""
    try:
        return await product_client.list_products(page=page, page_size=page_size)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Product catalog service unavailable: {exc}",
        ) from exc


@app.get("/api/v1/catalog/{product_id}")
async def get_catalog_item(product_id: str):
    """Fetch a single product through Product Service gRPC."""
    try:
        product = await product_client.get_product(product_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Product catalog service unavailable: {exc}",
        ) from exc
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


# ── Orders reverse proxy → Order Service HTTP ────────────


@app.get("/api/v1/orders", response_model=OrderListOut)
async def proxy_list_orders(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
):
    """List orders through the Order Service."""
    return await _proxy(request, f"{ORDER_SERVICE_HTTP_URL}/orders")


@app.post("/api/v1/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def proxy_create_order(
    payload: CreateOrderRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
):
    """Create an order through the Order Service."""
    return await _proxy(request, f"{ORDER_SERVICE_HTTP_URL}/orders")


@app.get("/api/v1/orders/{order_id}", response_model=OrderOut)
async def proxy_order_item(
    order_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
):
    """Fetch one order through the Order Service."""
    return await _proxy(request, f"{ORDER_SERVICE_HTTP_URL}/orders/{order_id}")


# ── Composite checkout ───────────────────────────────────


@app.post("/api/v1/checkout", status_code=status.HTTP_201_CREATED)
async def checkout_endpoint(
    payload: CheckoutRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
):
    """
    Composite checkout: validate JWT, check stock, then place the order.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer token header",
        )
    return await checkout(
        token=credentials.credentials,
        items=payload.items,
        http_client=_http_client(request),
        customer_name=payload.customer_name,
    )


if __name__ == "__main__":
    uvicorn.run(
        "api_gateway.main:app",
        host=HTTP_HOST,
        port=HTTP_PORT,
        reload=True,
    )
