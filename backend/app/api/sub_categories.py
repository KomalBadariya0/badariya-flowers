from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.category import CategoryRead
from app.schemas.common import ListResponse, MessageResponse
from app.schemas.sub_category import SubCategoryCreate, SubCategoryRead, SubCategoryUpdate
from app.services import category_service, sub_category_service
from app.utils.file_upload import IMAGE_EXTENSIONS, save_upload

router = APIRouter(prefix="/subcategories", tags=["Sub Categories"])


@router.get("", response_model=ListResponse[SubCategoryRead])
def list_sub_categories(
    search: Optional[str] = None,
    categoryId: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    rows, total = sub_category_service.list_sub_categories(
        db, search=search, category_id=categoryId, status_filter=status_filter
    )
    return {"data": rows, "total": total}


@router.get("/{sub_category_id}", response_model=SubCategoryRead)
def get_sub_category(sub_category_id: int, db: Session = Depends(get_db)):
    sub = sub_category_service.get_sub_category(db, sub_category_id)
    return sub_category_service.to_read(db, sub)


@router.post("", response_model=SubCategoryRead, status_code=status.HTTP_201_CREATED)
def create_sub_category(payload: SubCategoryCreate, db: Session = Depends(get_db)):
    sub = sub_category_service.create_sub_category(db, payload)
    return sub_category_service.to_read(db, sub)


@router.put("/{sub_category_id}", response_model=SubCategoryRead)
def update_sub_category(sub_category_id: int, payload: SubCategoryUpdate, db: Session = Depends(get_db)):
    sub = sub_category_service.update_sub_category(db, sub_category_id, payload)
    return sub_category_service.to_read(db, sub)


@router.delete("/{sub_category_id}", response_model=MessageResponse)
def delete_sub_category(sub_category_id: int, db: Session = Depends(get_db)):
    sub_category_service.delete_sub_category(db, sub_category_id)
    return MessageResponse(message="Sub category deleted")


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_sub_category_image(file: UploadFile = File(...)):
    url = await save_upload(file, "categories", allowed_extensions=IMAGE_EXTENSIONS, max_size_mb=2)
    return {"url": url}


@router.get("/meta/categories", response_model=ListResponse[CategoryRead])
def get_categories_for_dropdown(db: Session = Depends(get_db)):
    """Read-only helper for the admin 'Parent Category' dropdown — same
    data /api/categories returns, kept here too so sub-categories.js's
    SubCategoryAPI.getCategories() has a single obvious endpoint to call."""
    rows, total = category_service.list_categories(db)
    return {"data": rows, "total": total}