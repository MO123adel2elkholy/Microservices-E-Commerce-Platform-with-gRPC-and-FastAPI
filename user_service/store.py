"""Database-backed repository for User Service."""
import uuid
from typing import Optional
from sqlalchemy import select

from user_service.database import AsyncSessionLocal, init_db
from user_service.models_db import UserModel
from user_service.security import hash_password


async def seed_initial_users():
    """Ensure database has default seed users."""
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserModel).limit(1))
        existing = result.scalar_one_or_none()
        if existing:
            return  # Already seeded

        default_users = [
            UserModel(
                user_id="usr-admin01",
                email="admin@example.com",
                hashed_password=hash_password("adminpassword123"),
                full_name="Admin User",
                role="admin",
                is_active=True,
            ),
            UserModel(
                user_id="usr-alice01",
                email="alice@example.com",
                hashed_password=hash_password("alicepassword123"),
                full_name="Alice Wonderland",
                role="customer",
                is_active=True,
            ),
        ]
        session.add_all(default_users)
        await session.commit()


async def create_user(
    email: str,
    password: str,
    full_name: str,
    role: str = "customer",
) -> dict:
    """Create a new user in database. Raises ValueError if email is registered."""
    email_clean = email.strip().lower()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.email == email_clean)
        )
        if result.scalar_one_or_none():
            raise ValueError(f"User with email '{email}' already exists.")

        user_id = f"usr-{uuid.uuid4().hex[:8]}"
        hashed = hash_password(password)

        new_user = UserModel(
            user_id=user_id,
            email=email_clean,
            hashed_password=hashed,
            full_name=full_name.strip(),
            role=role,
            is_active=True,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user.to_dict()


async def get_user_by_email(email: str) -> Optional[dict]:
    """Look up a user by email."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.email == email.strip().lower())
        )
        user = result.scalar_one_or_none()
        return user.to_dict() if user else None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Look up a user by user_id."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.to_dict() if user else None


async def list_users() -> list[dict]:
    """Return all users in database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserModel))
        users = result.scalars().all()
        return [u.to_dict() for u in users]
