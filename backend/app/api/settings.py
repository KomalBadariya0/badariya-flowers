from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.services import settings_service, upload_service

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)


# ==========================================================
# Get Website Settings
# ==========================================================

@router.get("", response_model=SettingsRead)
def get_settings(db: Session = Depends(get_db)):
    settings = settings_service.get_or_create(db)
    return settings_service.to_read(settings)


# ==========================================================
# Update Website Settings
# ==========================================================

@router.put("", response_model=SettingsRead)
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
):
    settings = settings_service.update_settings(db, payload)
    return settings_service.to_read(settings)


# ==========================================================
# Upload Default Product Image
# ==========================================================

@router.post(
    "/image",
    status_code=status.HTTP_201_CREATED,
)
async def upload_default_product_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    POST /api/settings/image

    Upload default product image.
    """

    url = await upload_service.upload_default_product_image(
        db=db,
        file=file,
    )

    return {
        "success": True,
        "url": url,
    }