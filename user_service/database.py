"""Database setup for User Service using SQLAlchemy 2.0 Async."""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from user_service.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


async def init_db():
    """Create tables if they don't exist."""
    from user_service import models_db  # noqa: F401  — register models on Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
