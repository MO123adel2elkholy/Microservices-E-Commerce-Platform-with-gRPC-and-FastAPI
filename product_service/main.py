"""Product Service — FastAPI HTTP + gRPC server."""
import asyncio
from contextlib import asynccontextmanager

import grpc
import uvicorn
from fastapi import FastAPI, HTTPException, Query

from product_service import store
from product_service.config import GRPC_HOST, GRPC_PORT, HTTP_HOST, HTTP_PORT
from product_service.generated import product_pb2_grpc
from product_service.grpc_server import ProductServicer
from product_service.models import ProductListOut, ProductOut


# ── gRPC server lifecycle ────────────────────────────────


async def start_grpc_server() -> grpc.aio.Server:
    """Start the async gRPC server."""
    server = grpc.aio.server()
    product_pb2_grpc.add_ProductServiceServicer_to_server(
        ProductServicer(), server
    )
    listen_addr = f"{GRPC_HOST}:{GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    await server.start()
    print(f"[*] gRPC server listening on {listen_addr}")
    return server


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the catalog database and manage the gRPC server."""
    await store.seed_initial_products()
    grpc_server = await start_grpc_server()
    yield
    await grpc_server.stop(grace=5)
    print("[*] gRPC server stopped")


# ── FastAPI app ──────────────────────────────────────────

app = FastAPI(
    title="Product Service",
    description="Product catalog microservice with gRPC backend",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "product-service"}


@app.get("/products", response_model=ProductListOut)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """List all products with pagination."""
    products, total = await store.list_products(page, page_size)
    return ProductListOut(
        products=[
            ProductOut(
                **p,
                available=p["stock"] > 0,
            )
            for p in products
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@app.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: str):
    """Get a single product by ID."""
    product = await store.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductOut(**product, available=product["stock"] > 0)


# ── Entrypoint ───────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "product_service.main:app",
        host=HTTP_HOST,
        port=HTTP_PORT,
        reload=True,
    )
