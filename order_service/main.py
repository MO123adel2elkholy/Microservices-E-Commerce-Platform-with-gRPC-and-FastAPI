"""Order Service — FastAPI HTTP with gRPC clients to Product Service & User Service."""
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from order_service.config import HTTP_HOST, HTTP_PORT
from order_service.grpc_auth_client import user_client
from order_service.grpc_client import product_client
from order_service.models import (
    CreateOrderRequest,
    OrderItemOut,
    OrderListOut,
    OrderOut,
    OrderStatus,
)
from order_service import store

security_scheme = HTTPBearer(auto_error=False)


# ── Lifespan: manage gRPC client channels ────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the order database and open gRPC channels."""
    await store.init_store()
    await product_client.connect()
    await user_client.connect()
    yield
    await user_client.close()
    await product_client.close()


# ── FastAPI app ──────────────────────────────────────────

app = FastAPI(
    title="Order Service",
    description="Order management microservice — validates stock via Product Service gRPC and authenticates via User Service gRPC",
    version="1.0.0",
    lifespan=lifespan,
)


# ── gRPC Authentication Dependency ───────────────────────


async def get_current_user_from_grpc(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
) -> dict:
    """Validate incoming Bearer JWT token via gRPC call to User Service."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer token header",
        )

    try:
        token_info = await user_client.validate_token(credentials.credentials)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"User authentication service unavailable: {str(e)}",
        )

    if not token_info.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {token_info.get('message', 'Invalid token')}",
        )

    return token_info


# ── HTTP Endpoints ───────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "order-service"}


@app.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    current_user: dict = Depends(get_current_user_from_grpc),
):
    """
    Create an order.

    Requires Bearer JWT authenticated against User Service via gRPC.
    Each item is validated against Product Service via gRPC.
    """
    order_items: list[dict] = []
    total_amount = 0.0

    for item in request.items:
        try:
            validation = await product_client.validate_product(
                item.product_id, item.quantity
            )
            product = (
                await product_client.get_product(item.product_id)
                if validation["valid"]
                else None
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Product catalog service unavailable: {exc}",
            ) from exc

        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{item.product_id}': {validation['message']}",
            )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{item.product_id}' not found",
            )

        order_items.append(
            {
                "product_id": item.product_id,
                "product_name": product["name"],
                "quantity": item.quantity,
                "unit_price": validation["unit_price"],
                "total_price": validation["total_price"],
            }
        )
        total_amount += validation["total_price"]
    # Assign customer name from request or authenticated user profile
    customer_name = (
        request.customer_name
        or current_user.get("full_name")
        or current_user.get("email")
        or "Customer"
    )

    # Persist the order
    order = await store.create_order(
        customer_name=customer_name,
        items=order_items,
        total_amount=total_amount,
        user_id=current_user["user_id"],
    )

    return OrderOut(
        order_id=order["order_id"],
        customer_name=order["customer_name"],
        items=[OrderItemOut(**i) for i in order["items"]],
        total_amount=order["total_amount"],
        status=OrderStatus(order["status"]),
    )


@app.get("/orders", response_model=OrderListOut)
async def list_orders(
    current_user: dict = Depends(get_current_user_from_grpc),
):
    """List all orders (requires authentication)."""
    # Administrators can review all orders; customers only see their own.
    user_id = None if current_user.get("role") == "admin" else current_user["user_id"]
    orders = await store.list_orders(user_id=user_id)
    return OrderListOut(
        orders=[
            OrderOut(
                order_id=o["order_id"],
                customer_name=o["customer_name"],
                items=[OrderItemOut(**i) for i in o["items"]],
                total_amount=o["total_amount"],
                status=OrderStatus(o["status"]),
            )
            for o in orders
        ],
        total=len(orders),
    )


@app.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user_from_grpc),
):
    """Get a single order by ID (requires authentication)."""
    user_id = None if current_user.get("role") == "admin" else current_user["user_id"]
    order = await store.get_order(order_id, user_id=user_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return OrderOut(
        order_id=order["order_id"],
        customer_name=order["customer_name"],
        items=[OrderItemOut(**i) for i in order["items"]],
        total_amount=order["total_amount"],
        status=OrderStatus(order["status"]),
    )


# ── Entrypoint ───────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "order_service.main:app",
        host=HTTP_HOST,
        port=HTTP_PORT,
        reload=True,
    )
