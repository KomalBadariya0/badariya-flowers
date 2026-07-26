from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)

    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    sub_category_id = Column(Integer, ForeignKey("sub_categories.id", ondelete="CASCADE"), nullable=False, index=True)

    no = Column(Integer, nullable=False)  # article/display number within its sub category
    name = Column(String(200), nullable=False)
    sku = Column(String(100), nullable=True, unique=True, index=True)

    price = Column(Float, nullable=True)          # null = ask on WhatsApp / see price_note
    price_note = Column(String(255), nullable=True)
    moq = Column(Integer, nullable=False, default=1)

    short_desc = Column(Text, nullable=True)
    full_desc = Column(Text, nullable=True)

    material = Column(String(150), nullable=True)
    color = Column(String(150), nullable=True)
    weight = Column(String(80), nullable=True)
    dimensions = Column(String(150), nullable=True)

    tags = Column(JSON, nullable=True, default=list)              # ["genda", "toran"]
    specifications = Column(JSON, nullable=True, default=list)    # [{label, value}]
    features = Column(JSON, nullable=True, default=list)          # ["Handcrafted", ...]

    usage = Column(Text, nullable=True)
    care_instructions = Column(Text, nullable=True)

    seo_title = Column(String(255), nullable=True)
    seo_description = Column(String(500), nullable=True)
    seo_keywords = Column(String(255), nullable=True)
    seo_slug = Column(String(220), nullable=True, unique=False, index=True)

    featured = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    sub_category = relationship("SubCategory", back_populates="products")
    images = relationship(
        "ProductImage", back_populates="product", cascade="all, delete-orphan",
        passive_deletes=True, order_by="ProductImage.sort_order"
    )