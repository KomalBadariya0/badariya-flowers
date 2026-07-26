from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Catalogue(Base):
    """
    One row per PDF on the site:
      - type = "master"   -> the single full-catalogue PDF (category_id / sub_category_id are NULL)
      - type = "category" -> a per-sub-category PDF (sub_category_id is set)
    Re-uploading replaces file_url on the existing row rather than creating
    a new one (see CatalogueService.upload_*), so there is only ever one
    active PDF per (type, sub_category_id).
    """
    __tablename__ = "catalogues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(20), nullable=False, default="category")  # master | category

    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True)
    sub_category_id = Column(Integer, ForeignKey("sub_categories.id", ondelete="CASCADE"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category")
    sub_category = relationship("SubCategory")