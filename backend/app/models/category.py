from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    slug = Column(String(160), nullable=False, unique=True, index=True)
    tagline = Column(String(255), nullable=True)
    image = Column(String(500), nullable=True)  # cover image URL, served from /uploads/categories
    status = Column(String(20), nullable=False, default="active")  # active | inactive
    sort_order = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sub_categories = relationship(
        "SubCategory", back_populates="category", cascade="all, delete-orphan", passive_deletes=True
    )
    products = relationship("Product", back_populates="category")