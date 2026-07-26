"""
Admin > Catalogue PDF — server-rendered page + HTMX fragment endpoints.

This closes the one broken sidebar link found during the mobile/routing
audit: "Catalogue PDF" pointed at /admin/catalogue.html, a static file
that never existed (404 / "Cannot GET"). The catalogue business logic
already existed (app.services.catalogue_service, app.api.catalogues) —
only this admin UI was missing, so it is built here exactly the same
way as every other migrated module (Jinja2 + HTMX, same modal/toast
primitives from categories.css), calling the same service functions
the JSON API uses. No new business rules are introduced.

Route map (all under /admin/catalogue):
    GET    ""                                   full page
    GET    /master/upload-form                  upload/replace form fragment (master)
    POST   /master                               upload/replace master -> refreshed content
    GET    /subcategory/{sub_category_id}/upload-form  upload/replace form fragment (per sub-category)
    POST   /subcategory/{sub_category_id}        upload/replace -> refreshed content
    GET    /{catalogue_id}/confirm-delete        delete-confirm modal body fragment
    DELETE /{catalogue_id}                       delete -> refreshed content
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.catalogue import Catalogue
from app.services import catalogue_service, category_service, sub_category_service
from app.utils.file_upload import PDF_EXTENSIONS, get_file_size, save_upload
from app.web.deps import require_login, templates, toast_and_close

router = APIRouter(prefix="/admin/catalogue", tags=["Admin · Catalogue"], dependencies=[Depends(require_login)])


# ======================================================================
# shared context builder
# ======================================================================

def _content_context(db: Session) -> dict:
    master = catalogue_service.get_master(db)
    master_read = catalogue_service.to_read(master) if master else None

    sub_rows, _ = sub_category_service.list_sub_categories(db)
    category_rows, _ = category_service.list_categories(db)
    category_names = {c.id: c.name for c in category_rows}

    existing = {
        c.subCategoryId: c
        for c in catalogue_service.list_catalogues(db)
        if c.type == "category" and c.subCategoryId is not None
    }

    sub_catalogues = [
        {
            "sub": sub,
            "category_name": category_names.get(sub.categoryId, "—"),
            "catalogue": existing.get(sub.id),
        }
        for sub in sub_rows
    ]

    return {"master": master_read, "sub_catalogues": sub_catalogues}


# ======================================================================
# full page
# ======================================================================

@router.get("", response_class=HTMLResponse)
def catalogue_page(request: Request, db: Session = Depends(get_db)):
    ctx = _content_context(db)
    return templates.TemplateResponse(
        "admin/catalogue.html",
        {"request": request, "active_page": "catalogue", **ctx},
    )


# ======================================================================
# master catalogue: upload / replace
# ======================================================================

@router.get("/master/upload-form", response_class=HTMLResponse)
def master_upload_form(request: Request, db: Session = Depends(get_db)):
    master = catalogue_service.get_master(db)
    return templates.TemplateResponse(
        "admin/partials/catalogue_upload_form.html",
        {
            "request": request,
            "title_value": (master.title if master else "Badariya Flowers — Full Catalogue"),
            "action_url": "/admin/catalogue/master",
            "heading": "Upload Master Catalogue",
            "is_replace": master is not None,
        },
    )


@router.post("/master", response_class=HTMLResponse)
async def master_catalogue_upload(
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form("Badariya Flowers — Full Catalogue"),
    db: Session = Depends(get_db),
):
    url = await save_upload(file, "catalogues", allowed_extensions=PDF_EXTENSIONS, max_size_mb=20)
    size = get_file_size(url)
    catalogue_service.upsert_master(db, title=title or "Full Catalogue", file_url=url, file_size=size)
    ctx = _content_context(db)
    return templates.TemplateResponse(
        "admin/partials/catalogue_content.html",
        {"request": request, **ctx},
        headers=toast_and_close("Master catalogue uploaded", "catalogueUploadModal", toast_id="catalogueToast"),
    )


# ======================================================================
# per sub-category catalogue: upload / replace
# ======================================================================

@router.get("/subcategory/{sub_category_id}/upload-form", response_class=HTMLResponse)
def subcategory_upload_form(sub_category_id: int, request: Request, db: Session = Depends(get_db)):
    sub = sub_category_service.get_sub_category(db, sub_category_id)
    existing = db.query(Catalogue).filter(
        Catalogue.type == "category",
        Catalogue.sub_category_id == sub_category_id,
    ).first()
    return templates.TemplateResponse(
        "admin/partials/catalogue_upload_form.html",
        {
            "request": request,
            "title_value": (existing.title if existing else f"{sub.name} Catalogue"),
            "action_url": f"/admin/catalogue/subcategory/{sub_category_id}",
            "heading": f"Upload Catalogue — {sub.name}",
            "is_replace": existing is not None,
        },
    )


@router.post("/subcategory/{sub_category_id}", response_class=HTMLResponse)
async def subcategory_catalogue_upload(
    sub_category_id: int,
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    url = await save_upload(file, "catalogues", allowed_extensions=PDF_EXTENSIONS, max_size_mb=20)
    size = get_file_size(url)
    catalogue_service.upsert_category_catalogue(
        db, sub_category_id=sub_category_id, title=title or "Catalogue", file_url=url, file_size=size
    )
    ctx = _content_context(db)
    return templates.TemplateResponse(
        "admin/partials/catalogue_content.html",
        {"request": request, **ctx},
        headers=toast_and_close("Catalogue uploaded", "catalogueUploadModal", toast_id="catalogueToast"),
    )


# ======================================================================
# delete
# ======================================================================

@router.get("/{catalogue_id}/confirm-delete", response_class=HTMLResponse)
def catalogue_confirm_delete(catalogue_id: int, request: Request, db: Session = Depends(get_db)):
    row = catalogue_service.get_catalogue(db, catalogue_id)
    label = "Master Catalogue" if row.type == "master" else row.title
    return templates.TemplateResponse(
        "admin/partials/catalogue_delete_confirm.html",
        {"request": request, "catalogue_id": catalogue_id, "label": label},
    )


@router.delete("/{catalogue_id}", response_class=HTMLResponse)
def catalogue_delete(catalogue_id: int, request: Request, db: Session = Depends(get_db)):
    catalogue_service.delete_catalogue(db, catalogue_id)
    ctx = _content_context(db)
    return templates.TemplateResponse(
        "admin/partials/catalogue_content.html",
        {"request": request, **ctx},
        headers=toast_and_close("Catalogue PDF deleted", "catalogueDeleteModal", toast_id="catalogueToast"),
    )
