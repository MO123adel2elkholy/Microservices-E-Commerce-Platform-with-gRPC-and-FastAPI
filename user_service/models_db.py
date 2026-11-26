"""SQLAlchemy database models for User Service."""
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, String

from user_service.database import Base


class UserModel(Base):
    """User account entity in database."""

    __tablename__ = "users"

    user_id = Column(String(64), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="customer", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Convert ORM model to dictionary."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
