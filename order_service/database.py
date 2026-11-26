"""Database setup for Order Service using SQLAlchemy 2.0 Async."""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import declarative_base

from order_service.config import DATABASE_URL

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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # create_all does not alter existing tables. Add ownership tracking to
        # databases created by earlier versions without discarding their data.
        columns = await conn.run_sync(
            lambda sync_conn: {
                column["name"]
                for column in inspect(sync_conn).get_columns("orders")
            }
        )
        if "user_id" not in columns:
            await conn.execute(text("ALTER TABLE orders ADD COLUMN user_id VARCHAR(64)"))
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders (user_id)")
        )
