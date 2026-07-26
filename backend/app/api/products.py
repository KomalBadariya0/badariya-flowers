from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import ListResponse, MessageResponse
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.schemas.sub_category import SubCategoryRead
from app.services import product_service, sub_category_service
from app.utils.file_upload import IMAGE_EXTENSIONS, save_upload

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ListResponse[ProductRead])
def list_products(
    search: Optional[str] = None,
    categoryId: Optional[int] = Query(None),
    subCategoryId: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    featured: Optional[bool] = None,
    limit: Optional[int] = Query(None, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows, total = product_service.list_products(
        db, search=search, category_id=categoryId, sub_category_id=subCategoryId,
        status_filter=status_filter, featured=featured, limit=limit,
    )
    return {"data": rows, "total": total}


@router.get("/featured", response_model=ListResponse[ProductRead])
def list_featured_products(limit: int = Query(8, ge=1, le=50), db: Session = Depends(get_db)):
    rows, total = product_service.list_products(db, status_filter="active", featured=True, limit=limit)
    return {"data": rows, "total": total}


@router.get("/new-arrivals", response_model=ListResponse[ProductRead])
def list_new_arrivals(limit: int = Query(8, ge=1, le=50), db: Session = Depends(get_db)):
    rows, total = product_service.list_products(db, status_filter="active", limit=limit)
    return {"data": rows, "total": total}


@router.get("/lookup", response_model=ProductRead)
def lookup_product_by_no(subCategoryId: int, no: int, db: Session = Depends(get_db)):
    """Used by the customer website's product.html?sub=&no= permalinks,
    which address a product the same way the original hardcoded catalog.js
    did (sub category + display number) instead of the internal DB id."""
    product = product_service.get_product_by_no(db, subCategoryId, no)
    return product_service.to_read(product)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    return product_service.to_read(product)


@router.get("/{product_id}/related", response_model=List[ProductRead])
def get_related_products(product_id: int, limit: int = Query(8, ge=1, le=20), db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    return product_service.list_related(db, product, limit=limit)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = product_service.create_product(db, payload)
    return product_service.to_read(product)


@router.put("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = product_service.update_product(db, product_id, payload)
    return product_service.to_read(product)


@router.delete("/{product_id}", response_model=MessageResponse)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product_service.delete_product(db, product_id)
    return MessageResponse(message="Product deleted")


@router.get("/meta/subcategories", response_model=ListResponse[SubCategoryRead])
def get_sub_categories_for_dropdown(categoryId: Optional[int] = None, db: Session = Depends(get_db)):
    rows, total = sub_category_service.list_sub_categories(db, category_id=categoryId)
    return {"data": rows, "total": total}


@router.post("/upload-images", status_code=status.HTTP_201_CREATED)
async def upload_product_images(files: List[UploadFile] = File(...)):
    """Pre-upload for the product form: images are uploaded here first and
    the returned URLs are sent as `images` in the POST /products or
    PUT /products/{id} payload — matches ProductAPI.uploadImages(files) in
    admin/assets/js/product_store.js, which runs before the product itself
    is created or hasn't been assigned an id yet."""
    urls = []
    for file in files:
        url = await save_upload(file, "products", allowed_extensions=IMAGE_EXTENSIONS, max_size_mb=2)
        urls.append(url)
    return {"urls": urls}


@router.post("/{product_id}/images", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def attach_product_images(product_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Directly uploads and attaches images to an existing product (append,
    does not replace the current gallery)."""
    urls = []
    for file in files:
        url = await save_upload(file, "products", allowed_extensions=IMAGE_EXTENSIONS, max_size_mb=2)
        urls.append(url)
    product = product_service.append_images(db, product_id, urls)
    return product_service.to_read(product)


@router.delete("/{product_id}/images/{image_id}", response_model=ProductRead)
def delete_product_image(product_id: int, image_id: int, db: Session = Depends(get_db)):
    product = product_service.remove_image(db, product_id, image_id)
    return product_service.to_read(product)