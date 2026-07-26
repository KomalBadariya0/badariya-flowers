from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class SubCategory(Base):
    __tablename__ = "sub_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(150), nullable=False)
    slug = Column(String(160), nullable=False, unique=True, index=True)
    image = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="active")  # active | inactive
    sort_order = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="sub_categories")
    products = relationship(
        "Product", back_populates="sub_category", cascade="all, delete-orphan", passive_deletes=True
    )