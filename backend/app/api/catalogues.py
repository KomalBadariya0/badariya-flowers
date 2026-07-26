from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.catalogue import CatalogueRead
from app.schemas.common import MessageResponse
from app.services import catalogue_service
from app.utils.file_upload import PDF_EXTENSIONS, get_file_size, save_upload

router = APIRouter(prefix="/catalogues", tags=["Catalogues"])


@router.get("", response_model=List[CatalogueRead])
def list_catalogues(db: Session = Depends(get_db)):
    return catalogue_service.list_catalogues(db)


@router.get("/master", response_model=CatalogueRead)
def get_master_catalogue(db: Session = Depends(get_db)):
    row = catalogue_service.get_master(db)
    if not row:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="No master catalogue uploaded yet")
    return catalogue_service.to_read(row)


@router.get("/category/{sub_category_id}", response_model=CatalogueRead)
def get_category_catalogue(sub_category_id: int, db: Session = Depends(get_db)):
    row = catalogue_service.get_category_catalogue(db, sub_category_id)
    return catalogue_service.to_read(row)


@router.post("/master", response_model=CatalogueRead, status_code=status.HTTP_201_CREATED)
async def upload_master_catalogue(
    file: UploadFile = File(...),
    title: Optional[str] = Form("Badariya Flowers — Full Catalogue"),
    db: Session = Depends(get_db),
):
    url = await save_upload(file, "catalogues", allowed_extensions=PDF_EXTENSIONS, max_size_mb=20)
    size = get_file_size(url)
    row = catalogue_service.upsert_master(db, title=title or "Full Catalogue", file_url=url, file_size=size)
    return catalogue_service.to_read(row)


@router.post("/category/{sub_category_id}", response_model=CatalogueRead, status_code=status.HTTP_201_CREATED)
async def upload_category_catalogue(
    sub_category_id: int,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    url = await save_upload(file, "catalogues", allowed_extensions=PDF_EXTENSIONS, max_size_mb=20)
    size = get_file_size(url)
    row = catalogue_service.upsert_category_catalogue(
        db, sub_category_id=sub_category_id, title=title or "Catalogue", file_url=url, file_size=size
    )
    return catalogue_service.to_read(row)


@router.delete("/{catalogue_id}", response_model=MessageResponse)
def delete_catalogue(catalogue_id: int, db: Session = Depends(get_db)):
    catalogue_service.delete_catalogue(db, catalogue_id)
    return MessageResponse(message="Catalogue PDF deleted")