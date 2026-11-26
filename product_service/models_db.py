"""SQLAlchemy database models for Product Service."""
from sqlalchemy import Column, Float, Integer, String, Text

from product_service.database import Base


class ProductModel(Base):
    """Catalog item with inventory stock."""

    __tablename__ = "products"

    product_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)

    def to_dict(self) -> dict:
        """Convert ORM model to dictionary."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "stock": int(self.stock),
        }
