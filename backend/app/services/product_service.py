from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.sub_category import SubCategory
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate, SeoInfo, SpecificationItem


def _price_label(product: Product) -> str:
    if product.price is not None:
        return f"₹{product.price:g}"
    if product.price_note:
        return product.price_note
    return "Ask on WhatsApp"


def to_read(product: Product) -> ProductRead:
    images = [img.image_url for img in sorted(product.images, key=lambda i: i.sort_order)]
    return ProductRead(
        id=product.id,
        no=product.no,
        name=product.name,
        categoryId=product.category_id,
        subCategoryId=product.sub_category_id,
        sku=product.sku,
        price=product.price,
        priceNote=product.price_note,
        priceLabel=_price_label(product),
        moq=product.moq,
        shortDesc=product.short_desc,
        fullDesc=product.full_desc,
        material=product.material,
        color=product.color,
        weight=product.weight,
        dimensions=product.dimensions,
        tags=product.tags or [],
        images=images,
        featured=product.featured,
        active=product.active,
        specifications=[SpecificationItem(**s) for s in (product.specifications or [])],
        features=product.features or [],
        usage=product.usage,
        careInstructions=product.care_instructions,
        seo=SeoInfo(
            title=product.seo_title,
            description=product.seo_description,
            keywords=product.seo_keywords,
            slug=product.seo_slug,
        ),
        createdAt=product.created_at,
    )


def _base_query(db: Session):
    return db.query(Product).options(joinedload(Product.images))


def list_products(
    db: Session,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    sub_category_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    featured: Optional[bool] = None,
    limit: Optional[int] = None,
) -> Tuple[List[ProductRead], int]:
    query = _base_query(db)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(or_(Product.name.ilike(like), Product.sku.ilike(like)))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if sub_category_id is not None:
        query = query.filter(Product.sub_category_id == sub_category_id)
    if status_filter and status_filter != "all":
        query = query.filter(Product.active == (status_filter == "active"))
    if featured is not None:
        query = query.filter(Product.featured == featured)
    query = query.order_by(Product.sub_category_id.asc(), Product.no.asc())
    total = query.count()
    if limit:
        query = query.limit(limit)
    rows = query.all()
    return [to_read(p) for p in rows], total


def get_product(db: Session, product_id: int) -> Product:
    product = _base_query(db).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def get_product_by_no(db: Session, sub_category_id: int, no: int) -> Product:
    product = (
        _base_query(db)
        .filter(Product.sub_category_id == sub_category_id, Product.no == no)
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def list_related(db: Session, product: Product, limit: int = 8) -> List[ProductRead]:
    rows = (
        _base_query(db)
        .filter(
            Product.sub_category_id == product.sub_category_id,
            Product.id != product.id,
            Product.active.is_(True),
        )
        .limit(limit)
        .all()
    )
    return [to_read(p) for p in rows]


def _assert_sub_category_exists(db: Session, sub_category_id: int) -> SubCategory:
    sub = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sub category does not exist")
    return sub


def _assert_sku_unique(db: Session, sku: Optional[str], sub_category_id: Optional[int] = None, exclude_id: Optional[int] = None) -> None:
    if not sku:
        return
    query = db.query(Product).filter(func.lower(Product.sku) == sku.lower())
    if sub_category_id is not None:
        query = query.filter(Product.sub_category_id == sub_category_id)
    if exclude_id is not None:
        query = query.filter(Product.id != exclude_id)
    if query.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A product with this SKU already exists in this sub-category")


def _friendly_integrity_message(error: IntegrityError) -> str:
    """Maps a low-level DB integrity failure to a message the admin UI can
    show under the right field. SKU is the only column with a real DB-level
    unique constraint left (Product Name / Image / SEO Title / SEO
    Description / SEO Keywords / SEO Slug are all allowed to duplicate),
    but this stays generic so any future constraint fails safe too."""
    text = str(getattr(error, "orig", error)).lower()
    if "sku" in text:
        return "A product with this SKU already exists"
    return "This product could not be saved because of a conflicting value. Please check the form and try again."


def _next_no(db: Session, sub_category_id: int) -> int:
    max_no = db.query(func.max(Product.no)).filter(Product.sub_category_id == sub_category_id).scalar()
    return (max_no or 0) + 1


def _sync_images(db: Session, product: Product, urls: List[str]) -> None:
    """Replaces the product's images with the given ordered URL list — mirrors
    the frontend, which always resubmits the full state.images array on save."""
    db.query(ProductImage).filter(ProductImage.product_id == product.id).delete()
    for idx, url in enumerate(urls):
        db.add(ProductImage(product_id=product.id, image_url=url, sort_order=idx, is_primary=(idx == 0)))


def create_product(db: Session, payload: ProductCreate) -> Product:
    _assert_sub_category_exists(db, payload.subCategoryId)
    _assert_sku_unique(db, payload.sku, sub_category_id=payload.subCategoryId)

    seo = payload.seo or None
    product = Product(
        category_id=payload.categoryId,
        sub_category_id=payload.subCategoryId,
        no=_next_no(db, payload.subCategoryId),
        name=payload.name,
        sku=payload.sku,
        price=payload.price,
        price_note=payload.priceNote,
        moq=payload.moq,
        short_desc=payload.shortDesc,
        full_desc=payload.fullDesc,
        material=payload.material,
        color=payload.color,
        weight=payload.weight,
        dimensions=payload.dimensions,
        tags=payload.tags,
        specifications=[s.model_dump() for s in payload.specifications],
        features=payload.features,
        usage=payload.usage,
        care_instructions=payload.careInstructions,
        seo_title=seo.title if seo else payload.name,
        seo_description=seo.description if seo else payload.shortDesc,
        seo_keywords=seo.keywords if seo else None,
        seo_slug=seo.slug if seo else None,
        featured=payload.featured,
        active=payload.active,
    )
    db.add(product)
    try:
        db.flush()  # assigns product.id without committing yet
        _sync_images(db, product, payload.images)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=_friendly_integrity_message(exc)
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="We couldn't save the product right now. Please try again.",
        ) from exc
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, payload: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    _assert_sub_category_exists(db, payload.subCategoryId)
    _assert_sku_unique(db, payload.sku, sub_category_id=payload.subCategoryId, exclude_id=product_id)

    seo = payload.seo or None
    product.category_id = payload.categoryId
    product.sub_category_id = payload.subCategoryId
    product.name = payload.name
    product.sku = payload.sku
    product.price = payload.price
    product.price_note = payload.priceNote
    product.moq = payload.moq
    product.short_desc = payload.shortDesc
    product.full_desc = payload.fullDesc
    product.material = payload.material
    product.color = payload.color
    product.weight = payload.weight
    product.dimensions = payload.dimensions
    product.tags = payload.tags
    product.specifications = [s.model_dump() for s in payload.specifications]
    product.features = payload.features
    product.usage = payload.usage
    product.care_instructions = payload.careInstructions
    if seo:
        product.seo_title = seo.title or product.seo_title
        product.seo_description = seo.description or product.seo_description
        product.seo_keywords = seo.keywords or product.seo_keywords
        product.seo_slug = seo.slug or product.seo_slug
    product.featured = payload.featured
    product.active = payload.active

    try:
        _sync_images(db, product, payload.images)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=_friendly_integrity_message(exc)
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="We couldn't save the product right now. Please try again.",
        ) from exc
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = get_product(db, product_id)
    db.delete(product)
    db.commit()


def append_images(db: Session, product_id: int, urls: List[str]) -> Product:
    product = get_product(db, product_id)
    existing_count = len(product.images)
    for idx, url in enumerate(urls):
        db.add(
            ProductImage(
                product_id=product.id,
                image_url=url,
                sort_order=existing_count + idx,
                is_primary=(existing_count == 0 and idx == 0),
            )
        )
    db.commit()
    db.refresh(product)
    return product


def remove_image(db: Session, product_id: int, image_id: int) -> Product:
    product = get_product(db, product_id)
    image = db.query(ProductImage).filter(ProductImage.id == image_id, ProductImage.product_id == product_id).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found on this product")
    db.delete(image)
    db.commit()
    db.refresh(product)
    return product