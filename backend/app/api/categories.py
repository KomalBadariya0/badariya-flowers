from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import ListResponse, MessageResponse
from app.services import category_service
from app.utils.file_upload import IMAGE_EXTENSIONS, save_upload

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=ListResponse[CategoryRead])
def list_categories(
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    rows, total = category_service.list_categories(db, search=search, status_filter=status_filter)
    return {"data": rows, "total": total}


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = category_service.get_category(db, category_id)
    return category_service.to_read(db, category)


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    category = category_service.create_category(db, payload)
    return category_service.to_read(db, category)


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    category = category_service.update_category(db, category_id, payload)
    return category_service.to_read(db, category)


@router.delete("/{category_id}", response_model=MessageResponse)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category_service.delete_category(db, category_id)
    return MessageResponse(message="Category deleted")


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_category_image(file: UploadFile = File(...)):
    url = await save_upload(file, "categories", allowed_extensions=IMAGE_EXTENSIONS, max_size_mb=2)
    return {"url": url}