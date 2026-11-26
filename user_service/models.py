"""Pydantic models for User Service REST API."""
from typing import Literal
from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    """Payload for user registration."""

    email: str = Field(..., min_length=3, description="Valid email address")
    password: str = Field(..., min_length=6, description="Minimum 6 characters")
    full_name: str = Field(..., min_length=1, description="Full name")
    # Public registration must never grant administrative privileges.
    role: Literal["customer"] = "customer"


class UserLoginRequest(BaseModel):
    """Payload for user authentication."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """JWT Token response upon successful authentication."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    full_name: str


class UserOut(BaseModel):
    """User profile response model."""

    user_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
