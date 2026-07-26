from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services import upload_service

router = APIRouter(
    tags=["Uploads"],
)


# ==========================================================
# Upload Website Logo
# ==========================================================

@router.post(
    "/logo",
    status_code=status.HTTP_201_CREATED,
)
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    url = await upload_service.upload_logo(
        db=db,
        file=file,
    )

    return {
        "success": True,
        "url": url,
    }


# ==========================================================
# Upload Website Favicon
# ==========================================================

@router.post(
    "/favicon",
    status_code=status.HTTP_201_CREATED,
)
async def upload_favicon(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    url = await upload_service.upload_favicon(
        db=db,
        file=file,
    )

    return {
        "success": True,
        "url": url,
    }