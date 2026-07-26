"""
Upload Service

Handles:

- Website Logo Upload
- Website Favicon Upload
- Default Product Image Upload
"""

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.settings import SiteSettings
from app.services.settings_service import get_or_create
from app.utils.file_upload import (
    IMAGE_EXTENSIONS,
    FAVICON_EXTENSIONS,
    save_upload,
    delete_upload,
)


# ==========================================================
# Upload Website Logo
# ==========================================================

async def upload_logo(db: Session, file: UploadFile) -> str:
    settings = get_or_create(db)

    logo_url = await save_upload(
        file=file,
        folder="logos",
        allowed_extensions=IMAGE_EXTENSIONS,
        max_size_mb=2,
    )

    delete_upload(settings.logo_url)

    settings.logo_url = logo_url

    db.commit()
    db.refresh(settings)

    return logo_url


# ==========================================================
# Upload Website Favicon
# ==========================================================

async def upload_favicon(db: Session, file: UploadFile) -> str:
    settings = get_or_create(db)

    favicon_url = await save_upload(
        file=file,
        folder="logos",
        allowed_extensions=FAVICON_EXTENSIONS,
        max_size_mb=1,
    )

    delete_upload(settings.favicon_url)

    settings.favicon_url = favicon_url

    db.commit()
    db.refresh(settings)

    return favicon_url


# ==========================================================
# Upload Default Product Image
# ==========================================================

async def upload_default_product_image(
    db: Session,
    file: UploadFile,
) -> str:

    settings = get_or_create(db)

    image_url = await save_upload(
        file=file,
        folder="products",
        allowed_extensions=IMAGE_EXTENSIONS,
        max_size_mb=2,
    )

    delete_upload(settings.default_product_image_url)

    settings.default_product_image_url = image_url

    db.commit()
    db.refresh(settings)

    return image_url