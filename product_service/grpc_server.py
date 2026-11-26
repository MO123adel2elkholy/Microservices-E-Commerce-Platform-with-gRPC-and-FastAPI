"""gRPC servicer implementation for the Product Service."""
import grpc

from product_service.generated import product_pb2, product_pb2_grpc
from product_service import store


class ProductServicer(product_pb2_grpc.ProductServiceServicer):
    """Implements the ProductService gRPC interface."""

    async def GetProduct(self, request, context):
        """Fetch a single product by ID."""
        product = await store.get_product(request.product_id)
        if not product:
            await context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Product '{request.product_id}' not found",
            )
        return product_pb2.ProductResponse(
            product_id=product["product_id"],
            name=product["name"],
            description=product["description"],
            price=product["price"],
            stock=product["stock"],
            available=product["stock"] > 0,
        )

    async def ListProducts(self, request, context):
        """List products with pagination."""
        page = max(request.page, 1)
        page_size = min(max(request.page_size, 1), 100)
        products, total = await store.list_products(page, page_size)
        return product_pb2.ProductListResponse(
            products=[
                product_pb2.ProductResponse(
                    product_id=p["product_id"],
                    name=p["name"],
                    description=p["description"],
                    price=p["price"],
                    stock=p["stock"],
                    available=p["stock"] > 0,
                )
                for p in products
            ],
            total=total,
        )

    async def ValidateProduct(self, request, context):
        """Validate product availability and return pricing info."""
        valid, message, unit_price = await store.validate_product(
            request.product_id, request.quantity
        )
        return product_pb2.ProductValidationResponse(
            valid=valid,
            message=message,
            unit_price=unit_price,
            total_price=unit_price * request.quantity if valid else 0.0,
        )
