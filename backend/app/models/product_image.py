from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class ProductImage(Base):
    """
    One row per product photo. `sort_order` drives gallery order (the
    frontend always resubmits the full ordered `images` URL list on save —
    see ProductService._sync_images), and `is_primary` marks the image
    used as the product's card/list thumbnail.
    """
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    image_url = Column(String(500), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_primary = Column(Boolean, nullable=False, default=False)

    product = relationship("Product", back_populates="images")