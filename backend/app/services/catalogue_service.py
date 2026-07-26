from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.catalogue import Catalogue
from app.models.sub_category import SubCategory
from app.schemas.catalogue import CatalogueRead
from app.utils.file_upload import delete_upload


def to_read(catalogue: Catalogue) -> CatalogueRead:
    return CatalogueRead(
        id=catalogue.id,
        type=catalogue.type,
        categoryId=catalogue.category_id,
        subCategoryId=catalogue.sub_category_id,
        title=catalogue.title,
        fileUrl=catalogue.file_url,
        fileSize=catalogue.file_size,
        uploadedAt=catalogue.uploaded_at,
    )


def list_catalogues(db: Session) -> List[CatalogueRead]:
    rows = db.query(Catalogue).order_by(Catalogue.uploaded_at.desc()).all()
    return [to_read(c) for c in rows]


def get_master(db: Session) -> Optional[Catalogue]:
    return db.query(Catalogue).filter(Catalogue.type == "master").first()


def get_category_catalogue(db: Session, sub_category_id: int) -> Catalogue:
    row = db.query(Catalogue).filter(Catalogue.type == "category", Catalogue.sub_category_id == sub_category_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No catalogue uploaded for this sub category yet")
    return row


def upsert_master(db: Session, title: str, file_url: str, file_size: int) -> Catalogue:
    row = get_master(db)
    if row:
        delete_upload(row.file_url)
        row.title = title
        row.file_url = file_url
        row.file_size = file_size
    else:
        row = Catalogue(type="master", title=title, file_url=file_url, file_size=file_size)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def upsert_category_catalogue(db: Session, sub_category_id: int, title: str, file_url: str, file_size: int) -> Catalogue:
    sub = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sub category does not exist")

    row = db.query(Catalogue).filter(Catalogue.type == "category", Catalogue.sub_category_id == sub_category_id).first()
    if row:
        delete_upload(row.file_url)
        row.title = title
        row.file_url = file_url
        row.file_size = file_size
    else:
        row = Catalogue(
            type="category", category_id=sub.category_id, sub_category_id=sub_category_id,
            title=title, file_url=file_url, file_size=file_size,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_catalogue(db: Session, catalogue_id: int) -> Catalogue:
    row = db.query(Catalogue).filter(Catalogue.id == catalogue_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalogue PDF not found")
    return row


def delete_catalogue(db: Session, catalogue_id: int) -> None:
    row = get_catalogue(db, catalogue_id)
    delete_upload(row.file_url)
    db.delete(row)
    db.commit()