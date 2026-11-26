"""Tests for the Product Service REST API."""
import pytest
from fastapi.testclient import TestClient

from product_service.main import app

client = TestClient(app)


def test_health_check():
    """Product service health endpoint returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "product-service"


def test_list_products():
    """List products returns all seeded products."""
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert len(data["products"]) == 4


def test_list_products_pagination():
    """Pagination returns the correct page size."""
    response = client.get("/products?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["products"]) == 2
    assert data["total"] == 4
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_get_product_found():
    """Getting an existing product returns 200 with correct data."""
    response = client.get("/products/prod-001")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Wireless Headphones"
    assert data["price"] == 79.99
    assert data["available"] is True


def test_get_product_out_of_stock():
    """Out-of-stock product is returned but marked unavailable."""
    response = client.get("/products/prod-004")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Webcam 4K"
    assert data["stock"] == 0
    assert data["available"] is False


def test_get_product_not_found():
    """Requesting a non-existent product returns 404."""
    response = client.get("/products/nonexistent")
    assert response.status_code == 404
