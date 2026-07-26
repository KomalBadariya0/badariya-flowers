from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.models.sub_category import SubCategory
from app.schemas.sub_category import SubCategoryCreate, SubCategoryRead, SubCategoryUpdate


def _total_products(db: Session, sub_category_id: int) -> int:
    return db.query(func.count(Product.id)).filter(Product.sub_category_id == sub_category_id).scalar() or 0


def to_read(db: Session, sub: SubCategory) -> SubCategoryRead:
    return SubCategoryRead(
        id=sub.id,
        name=sub.name,
        categoryId=sub.category_id,
        slug=sub.slug,
        image=sub.image,
        totalProducts=_total_products(db, sub.id),
        status=sub.status,
        sortOrder=sub.sort_order,
        createdAt=sub.created_at,
        updatedAt=sub.updated_at,
    )


def _assert_category_exists(db: Session, category_id: int) -> None:
    if not db.query(Category).filter(Category.id == category_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent category does not exist")


def list_sub_categories(
    db: Session,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    status_filter: Optional[str] = None,
) -> Tuple[List[SubCategoryRead], int]:
    query = db.query(SubCategory)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(or_(SubCategory.name.ilike(like), SubCategory.slug.ilike(like)))
    if category_id is not None:
        query = query.filter(SubCategory.category_id == category_id)
    if status_filter and status_filter != "all":
        query = query.filter(SubCategory.status == status_filter)
    rows = query.order_by(SubCategory.sort_order.asc()).all()
    return [to_read(db, s) for s in rows], len(rows)


def get_sub_category(db: Session, sub_category_id: int) -> SubCategory:
    sub = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sub category not found")
    return sub


def _assert_unique(db: Session, payload: SubCategoryCreate, exclude_id: Optional[int] = None) -> None:
    slug_query = db.query(SubCategory).filter(SubCategory.slug == payload.slug)
    name_query = db.query(SubCategory).filter(
        SubCategory.category_id == payload.categoryId, func.lower(SubCategory.name) == payload.name.lower()
    )
    if exclude_id is not None:
        slug_query = slug_query.filter(SubCategory.id != exclude_id)
        name_query = name_query.filter(SubCategory.id != exclude_id)
    if slug_query.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A sub category with this slug already exists")
    if name_query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="This category already has a sub category with this name"
        )


def create_sub_category(db: Session, payload: SubCategoryCreate) -> SubCategory:
    _assert_category_exists(db, payload.categoryId)
    _assert_unique(db, payload)
    sub = SubCategory(
        name=payload.name,
        category_id=payload.categoryId,
        slug=payload.slug,
        image=payload.image,
        status=payload.status,
        sort_order=payload.sortOrder,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def update_sub_category(db: Session, sub_category_id: int, payload: SubCategoryUpdate) -> SubCategory:
    sub = get_sub_category(db, sub_category_id)
    _assert_category_exists(db, payload.categoryId)
    _assert_unique(db, payload, exclude_id=sub_category_id)
    sub.name = payload.name
    sub.category_id = payload.categoryId
    sub.slug = payload.slug
    sub.image = payload.image or sub.image
    sub.status = payload.status
    sub.sort_order = payload.sortOrder
    db.commit()
    db.refresh(sub)
    return sub


def delete_sub_category(db: Session, sub_category_id: int) -> None:
    sub = get_sub_category(db, sub_category_id)
    db.delete(sub)
    db.commit()