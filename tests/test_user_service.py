"""Tests for the User Service REST API and gRPC Servicer."""
import pytest
from fastapi.testclient import TestClient

from user_service.main import app
from user_service.grpc_server import UserServicer
from user_service.security import create_access_token
from user_service.generated import user_pb2
import grpc

client = TestClient(app)


def test_health_check():
    """User service health probe returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "user-service"


def test_register_user_success():
    """Registering a new user account succeeds."""
    payload = {
        "email": "charlie@example.com",
        "password": "secretpassword123",
        "full_name": "Charlie Brown",
        "role": "customer",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "charlie@example.com"
    assert data["full_name"] == "Charlie Brown"
    assert data["role"] == "customer"
    assert "user_id" in data


def test_register_duplicate_user_fails():
    """Registering with an already existing email returns 400."""
    payload = {
        "email": "admin@example.com",  # Already seeded
        "password": "newpassword123",
        "full_name": "Another Admin",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success():
    """Logging in with valid credentials returns a signed JWT."""
    payload = {
        "email": "alice@example.com",
        "password": "alicepassword123",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "customer"


def test_login_invalid_password_fails():
    """Logging in with wrong credentials returns 401."""
    payload = {
        "email": "alice@example.com",
        "password": "wrongpassword!",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_get_me_authenticated():
    """Accessing /auth/me with a valid Bearer token returns profile."""
    # First login to get a fresh token
    login_res = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "alicepassword123"},
    )
    token = login_res.json()["access_token"]

    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Wonderland"


def test_get_me_unauthorized():
    """Accessing /auth/me without a Bearer token returns 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_grpc_validate_token_success():
    """Direct gRPC call to ValidateToken returns valid=True for valid JWT."""
    token = create_access_token(
        {"sub": "usr-alice01", "email": "alice@example.com", "role": "customer"}
    )
    servicer = UserServicer()
    request = user_pb2.ValidateTokenRequest(token=token)

    response = await servicer.ValidateToken(request, None)
    assert response.valid is True
    assert response.user_id == "usr-alice01"
    assert response.email == "alice@example.com"
    assert response.role == "customer"


@pytest.mark.asyncio
async def test_grpc_validate_token_invalid():
    """Direct gRPC call to ValidateToken returns valid=False for forged token."""
    servicer = UserServicer()
    request = user_pb2.ValidateTokenRequest(token="invalid.tampered.token")

    response = await servicer.ValidateToken(request, None)
    assert response.valid is False
    assert "Invalid" in response.message
