"""
Shared upload helpers used by the categories / products / catalogues /
settings (logo, favicon) routers.

Files are saved to backend/uploads/<subdir>/<uuid>.<ext> on disk and
served back at /uploads/<subdir>/<uuid>.<ext> — main.py mounts the
uploads/ folder as static files at that path. Only the *relative* URL
(e.g. "/uploads/products/ab12cd.png") is ever stored in the database, so
moving the upload root or fronting it with a CDN later needs no schema
change — just update how the URL is built here.
"""
import uuid
from pathlib import Path
from typing import Iterable, Optional

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
FAVICON_EXTENSIONS = {".png", ".ico"}
PDF_EXTENSIONS = {".pdf"}


def _validate_extension(filename: str, allowed: Iterable[str]) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext or 'unknown'}'. Allowed: {', '.join(sorted(allowed))}",
        )
    return ext


async def _read_and_validate_size(file: UploadFile, max_bytes: int) -> bytes:
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(content) > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is too large. Maximum allowed size is {max_mb:.1f}MB",
        )
    return content


async def save_upload(
    file: UploadFile,
    subdir: str,
    allowed_extensions: Iterable[str] = IMAGE_EXTENSIONS,
    max_size_mb: Optional[float] = None,
) -> str:
    """
    Validates and saves an UploadFile under uploads/<subdir>/, returning
    the relative URL to store on the model (e.g. "/uploads/products/…").
    """
    max_bytes = int((max_size_mb or settings.MAX_IMAGE_SIZE_MB) * 1024 * 1024)
    ext = _validate_extension(file.filename, allowed_extensions)
    content = await _read_and_validate_size(file, max_bytes)

    target_dir = settings.upload_root / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    target_path = target_dir / filename
    target_path.write_bytes(content)

    return f"/uploads/{subdir}/{filename}"


def get_file_size(url: Optional[str]) -> Optional[int]:
    """Returns the size in bytes of a previously-saved file given its stored
    URL (e.g. \"/uploads/catalogues/…\"). Used by callers that need the size
    for the DB record but can't re-read the UploadFile stream after
    save_upload() has already consumed it. Returns None for empty/external/
    malformed URLs or if the file can't be found."""
    if not url or not url.startswith("/uploads/"):
        return None
    file_path = settings.upload_root.parent / url.lstrip("/")
    try:
        if file_path.is_file():
            return file_path.stat().st_size
    except OSError:
        pass
    return None


def delete_upload(url: Optional[str]) -> None:
    """Best-effort delete of a previously-saved file given its stored URL.
    Silently no-ops for empty/external/malformed URLs so callers never
    need to wrap this in their own try/except."""
    if not url or not url.startswith("/uploads/"):
        return
    file_path = settings.upload_root.parent / url.lstrip("/")
    try:
        if file_path.is_file():
            file_path.unlink()
    except OSError:
        pass