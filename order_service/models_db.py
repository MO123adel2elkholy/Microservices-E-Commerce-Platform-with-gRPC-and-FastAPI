"""SQLAlchemy database models for Order Service."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from order_service.database import Base


class OrderModel(Base):
    """Persisted customer order."""

    __tablename__ = "orders"

    order_id = Column(String(64), primary_key=True, index=True)
    # Nullable for orders created before ownership tracking was introduced.
    user_id = Column(String(64), nullable=True)
    customer_name = Column(String(255), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="confirmed")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    items = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        """Convert ORM model to dictionary including line items."""
        return {
            "order_id": self.order_id,
            "customer_name": self.customer_name,
            "items": [item.to_dict() for item in self.items],
            "total_amount": float(self.total_amount),
            "status": self.status,
        }


class OrderItemModel(Base):
    """Line item belonging to an order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(
        String(64),
        ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(String(64), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    order = relationship("OrderModel", back_populates="items")

    def to_dict(self) -> dict:
        """Convert line item to dictionary."""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": int(self.quantity),
            "unit_price": float(self.unit_price),
            "total_price": float(self.total_price),
        }
