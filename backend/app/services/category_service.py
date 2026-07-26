from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate


def _total_products(db: Session, category_id: int) -> int:
    return db.query(func.count(Product.id)).filter(Product.category_id == category_id).scalar() or 0


def to_read(db: Session, category: Category) -> CategoryRead:
    return CategoryRead(
        id=category.id,
        name=category.name,
        slug=category.slug,
        tagline=category.tagline,
        image=category.image,
        totalProducts=_total_products(db, category.id),
        status=category.status,
        sortOrder=category.sort_order,
        createdAt=category.created_at,
        updatedAt=category.updated_at,
    )


def list_categories(
    db: Session, search: Optional[str] = None, status_filter: Optional[str] = None
) -> Tuple[List[CategoryRead], int]:
    query = db.query(Category)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(or_(Category.name.ilike(like), Category.slug.ilike(like)))
    if status_filter and status_filter != "all":
        query = query.filter(Category.status == status_filter)
    rows = query.order_by(Category.sort_order.asc()).all()
    return [to_read(db, c) for c in rows], len(rows)


def get_category(db: Session, category_id: int) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


def _assert_unique(db: Session, payload: CategoryCreate, exclude_id: Optional[int] = None) -> None:
    slug_query = db.query(Category).filter(Category.slug == payload.slug)
    name_query = db.query(Category).filter(func.lower(Category.name) == payload.name.lower())
    if exclude_id is not None:
        slug_query = slug_query.filter(Category.id != exclude_id)
        name_query = name_query.filter(Category.id != exclude_id)
    if slug_query.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A category with this slug already exists")
    if name_query.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A category with this name already exists")


def create_category(db: Session, payload: CategoryCreate) -> Category:
    _assert_unique(db, payload)
    category = Category(
        name=payload.name,
        slug=payload.slug,
        tagline=payload.tagline,
        image=payload.image,
        status=payload.status,
        sort_order=payload.sortOrder,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, payload: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    _assert_unique(db, payload, exclude_id=category_id)
    category.name = payload.name
    category.slug = payload.slug
    category.tagline = payload.tagline
    category.image = payload.image or category.image
    category.status = payload.status
    category.sort_order = payload.sortOrder
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    db.delete(category)
    db.commit()


def next_sort_order(db: Session) -> int:
    """Default sort order suggested on the 'Add Category' form —
    mirrors the old frontend's `state.rows.length + 1` behaviour."""
    return (db.query(func.count(Category.id)).scalar() or 0) + 1