"""Composite checkout workflow: auth → stock check → order placement."""
from typing import Optional

import httpx
from fastapi import HTTPException, status

from api_gateway.clients import product_client, user_client
from api_gateway.config import ORDER_SERVICE_HTTP_URL
from api_gateway.models import CheckoutItem


async def checkout(
    token: str,
    items: list[CheckoutItem],
    http_client: httpx.AsyncClient,
    customer_name: Optional[str] = None,
) -> dict:
    """
    Orchestrate checkout across User, Product, and Order services.

    1. Validate the Bearer token via User Service gRPC.
    2. Validate stock for every item via Product Service gRPC.
    3. Place the order via Order Service HTTP.
    """
    try:
        token_info = await user_client.validate_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"User authentication service unavailable: {exc}",
        ) from exc

    if not token_info.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {token_info.get('message', 'Invalid token')}",
        )

    for item in items:
        try:
            validation = await product_client.validate_product(
                item.product_id, item.quantity
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Product catalog service unavailable: {exc}",
            ) from exc

        if not validation.get("valid"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{item.product_id}': {validation.get('message', 'unavailable')}",
            )

    payload = {
        "customer_name": customer_name,
        "items": [
            {"product_id": item.product_id, "quantity": item.quantity} for item in items
        ],
    }
    try:
        response = await http_client.post(
            f"{ORDER_SERVICE_HTTP_URL}/orders",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Order service unavailable: {exc}",
        ) from exc

    if response.status_code >= 400:
        detail = _extract_detail(response)
        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()


def _extract_detail(response: httpx.Response):
    try:
        body = response.json()
        return body.get("detail", body)
    except ValueError:
        return response.text
