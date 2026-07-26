"""
Admin > Sub Categories — server-rendered page + HTMX fragment endpoints.

Mirrors app/web/admin_categories.py exactly (same route shapes, same
HX-Trigger conventions, same modal open/close pattern). The only
addition is the parent Category dropdown, since a Sub Category always
belongs to one Category.

All business logic / validation / DB access is delegated to the
existing app.services.sub_category_service (unchanged) and
app.services.category_service (reused only to list categories for the
parent dropdown) — nothing here duplicates that logic.

Route map (all under /admin/subcategories):
    GET    ""                     full page (table + both modals, empty)
    GET    /rows                  <tbody> fragment — search / category filter
    GET    /new                   Add-Sub-Category form fragment
    GET    /{id}/edit             Edit-Sub-Category form fragment (prefilled)
    POST   ""                     create -> returns refreshed rows fragment
    PUT    /{id}                  update -> returns refreshed rows fragment
    DELETE /{id}                  delete -> returns refreshed rows fragment
    GET    /{id}/view             View-Sub-Category modal body fragment
    GET    /{id}/confirm-delete   Delete-confirm modal body fragment
    POST   /{id}/toggle-status    flips active/inactive -> single <tr> fragment
    POST   /upload-image          image upload -> preview fragment
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.sub_category import SubCategoryCreate, SubCategoryUpdate
from app.services import category_service, sub_category_service
from app.utils.file_upload import IMAGE_EXTENSIONS, save_upload
from app.web.deps import require_login, retarget_header, templates, toast_and_close, toast_only

router = APIRouter(prefix="/admin/subcategories", tags=["Admin · Sub Categories"], dependencies=[Depends(require_login)])


# ======================================================================
# helpers
# ======================================================================

def _rows_context(db: Session, search: Optional[str], category_id: Optional[int]) -> dict:
    rows, total = sub_category_service.list_sub_categories(db, search=search, category_id=category_id)
    return {"rows": rows, "total": total, "categories": _category_options(db)}


def _category_options(db: Session):
    """All categories, for the parent-category <select> — reuses the
    exact same service function app.web.admin_categories relies on."""
    rows, _ = category_service.list_categories(db)
    return rows


def _field_errors_from_validation_error(exc: ValidationError) -> dict:
    errors = {}
    for err in exc.errors():
        field = err["loc"][-1]
        errors[field] = err["msg"]
    return errors


async def _build_payload_or_errors(
    name: str,
    category_id: str,
    slug: str,
    status_value: str,
    sort_order: str,
    image: Optional[str],
    schema_cls,
):
    """Runs the exact same SubCategoryCreate/SubCategoryUpdate pydantic
    validation the JSON API uses, from HTML form fields."""
    try:
        sort_order_int = int(sort_order) if str(sort_order).strip() else 1
    except ValueError:
        sort_order_int = 1
    try:
        category_id_int = int(category_id) if str(category_id).strip() else 0
    except ValueError:
        category_id_int = 0
    try:
        payload = schema_cls(
            name=name,
            categoryId=category_id_int,
            slug=slug,
            image=image or None,
            status=status_value or "active",
            sortOrder=sort_order_int,
        )
        return payload, {}
    except ValidationError as exc:
        return None, _field_errors_from_validation_error(exc)


# ======================================================================
# full page
# ======================================================================

@router.get("", response_class=HTMLResponse)
def sub_categories_page(request: Request, db: Session = Depends(get_db)):
    ctx = _rows_context(db, search=None, category_id=None)
    return templates.TemplateResponse(
        "admin/subcategories.html",
        {"request": request, "active_page": "subcategories", **ctx},
    )


# ======================================================================
# table rows (search / category filter)
# ======================================================================

@router.get("/rows", response_class=HTMLResponse)
def sub_categories_rows(
    request: Request,
    search: Optional[str] = None,
    categoryId: Optional[str] = None,
    db: Session = Depends(get_db),
):
    cat_id = int(categoryId) if categoryId and categoryId != "all" else None
    ctx = _rows_context(db, search=search, category_id=cat_id)
    return templates.TemplateResponse(
        "admin/partials/sub_category_rows.html", {"request": request, **ctx}
    )


# ======================================================================
# add / edit form fragments
# ======================================================================

@router.get("/new", response_class=HTMLResponse)
def sub_category_form_new(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "admin/partials/sub_category_form.html",
        {
            "request": request,
            "mode": "add",
            "sub_category": None,
            "categories": _category_options(db),
            "next_sort_order": sub_category_service.list_sub_categories(db)[1] + 1,
            "errors": {},
        },
    )


@router.get("/{sub_category_id}/edit", response_class=HTMLResponse)
def sub_category_form_edit(sub_category_id: int, request: Request, db: Session = Depends(get_db)):
    sub = sub_category_service.get_sub_category(db, sub_category_id)
    sub_read = sub_category_service.to_read(db, sub)
    return templates.TemplateResponse(
        "admin/partials/sub_category_form.html",
        {
            "request": request,
            "mode": "edit",
            "sub_category": sub_read,
            "categories": _category_options(db),
            "next_sort_order": sub_read.sortOrder,
            "errors": {},
        },
    )


# ======================================================================
# create / update / delete
# ======================================================================

@router.post("", response_class=HTMLResponse)
async def sub_category_create(
    request: Request,
    name: str = Form(""),
    categoryId: str = Form(""),
    slug: str = Form(""),
    status_value: str = Form("active", alias="status"),
    sortOrder: str = Form("1"),
    image: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    payload, errors = await _build_payload_or_errors(
        name, categoryId, slug, status_value, sortOrder, image, SubCategoryCreate
    )
    form_values = {"name": name, "categoryId": categoryId, "slug": slug, "status": status_value,
                    "sortOrder": sortOrder, "image": image}
    if errors:
        return templates.TemplateResponse(
            "admin/partials/sub_category_form.html",
            {"request": request, "mode": "add", "sub_category": None, "categories": _category_options(db),
             "next_sort_order": sortOrder, "errors": errors, "form_values": form_values},
            headers=retarget_header("#subCategoryForm"),
        )
    try:
        sub_category_service.create_sub_category(db, payload)
    except HTTPException as exc:  # duplicate name/slug or missing parent category -> 400
        field = "slug" if "slug" in str(exc.detail).lower() else (
            "categoryId" if "category" in str(exc.detail).lower() else "name"
        )
        return templates.TemplateResponse(
            "admin/partials/sub_category_form.html",
            {"request": request, "mode": "add", "sub_category": None, "categories": _category_options(db),
             "next_sort_order": sortOrder, "errors": {field: exc.detail}, "form_values": form_values},
            headers=retarget_header("#subCategoryForm"),
        )
    ctx = _rows_context(db, search=None, category_id=None)
    return templates.TemplateResponse(
        "admin/partials/sub_category_rows.html",
        {"request": request, **ctx},
        headers=toast_and_close("Sub category added successfully", "subCategoryFormModal", toast_id="subCategoryToast"),
    )


@router.put("/{sub_category_id}", response_class=HTMLResponse)
async def sub_category_update(
    sub_category_id: int,
    request: Request,
    name: str = Form(""),
    categoryId: str = Form(""),
    slug: str = Form(""),
    status_value: str = Form("active", alias="status"),
    sortOrder: str = Form("1"),
    image: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    payload, errors = await _build_payload_or_errors(
        name, categoryId, slug, status_value, sortOrder, image, SubCategoryUpdate
    )
    form_values = {"name": name, "categoryId": categoryId, "slug": slug, "status": status_value,
                    "sortOrder": sortOrder, "image": image}
    if errors:
        existing = sub_category_service.to_read(db, sub_category_service.get_sub_category(db, sub_category_id))
        return templates.TemplateResponse(
            "admin/partials/sub_category_form.html",
            {"request": request, "mode": "edit", "sub_category": existing, "categories": _category_options(db),
             "next_sort_order": sortOrder, "errors": errors, "form_values": form_values},
            headers=retarget_header("#subCategoryForm"),
        )
    try:
        sub_category_service.update_sub_category(db, sub_category_id, payload)
    except HTTPException as exc:
        field = "slug" if "slug" in str(exc.detail).lower() else (
            "categoryId" if "category" in str(exc.detail).lower() else "name"
        )
        existing = sub_category_service.to_read(db, sub_category_service.get_sub_category(db, sub_category_id))
        return templates.TemplateResponse(
            "admin/partials/sub_category_form.html",
            {"request": request, "mode": "edit", "sub_category": existing, "categories": _category_options(db),
             "next_sort_order": sortOrder, "errors": {field: exc.detail}, "form_values": form_values},
            headers=retarget_header("#subCategoryForm"),
        )
    ctx = _rows_context(db, search=None, category_id=None)
    return templates.TemplateResponse(
        "admin/partials/sub_category_rows.html",
        {"request": request, **ctx},
        headers=toast_and_close("Sub category updated successfully", "subCategoryFormModal", toast_id="subCategoryToast"),
    )


@router.delete("/{sub_category_id}", response_class=HTMLResponse)
def sub_category_delete(sub_category_id: int, request: Request, db: Session = Depends(get_db)):
    sub_category_service.delete_sub_category(db, sub_category_id)
    ctx = _rows_context(db, search=None, category_id=None)
    return templates.TemplateResponse(
        "admin/partials/sub_category_rows.html",
        {"request": request, **ctx},
        headers=toast_and_close("Sub category deleted", "subCategoryDeleteModal", toast_id="subCategoryToast"),
    )


# ======================================================================
# view / delete-confirm fragments
# ======================================================================

@router.get("/{sub_category_id}/view", response_class=HTMLResponse)
def sub_category_view(sub_category_id: int, request: Request, db: Session = Depends(get_db)):
    sub = sub_category_service.get_sub_category(db, sub_category_id)
    sub_read = sub_category_service.to_read(db, sub)
    parent = category_service.get_category(db, sub_read.categoryId)
    return templates.TemplateResponse(
        "admin/partials/sub_category_view.html",
        {"request": request, "sub_category": sub_read, "parent_category": parent},
    )


@router.get("/{sub_category_id}/confirm-delete", response_class=HTMLResponse)
def sub_category_confirm_delete(sub_category_id: int, request: Request, db: Session = Depends(get_db)):
    sub = sub_category_service.get_sub_category(db, sub_category_id)
    sub_read = sub_category_service.to_read(db, sub)
    return templates.TemplateResponse(
        "admin/partials/sub_category_delete_confirm.html", {"request": request, "sub_category": sub_read}
    )


# ======================================================================
# toggle status (single row swap)
# ======================================================================

@router.post("/{sub_category_id}/toggle-status", response_class=HTMLResponse)
def sub_category_toggle_status(sub_category_id: int, request: Request, db: Session = Depends(get_db)):
    sub = sub_category_service.get_sub_category(db, sub_category_id)
    sub_read = sub_category_service.to_read(db, sub)
    next_status = "inactive" if sub_read.status == "active" else "active"
    update_payload = SubCategoryUpdate(
        name=sub_read.name, categoryId=sub_read.categoryId, slug=sub_read.slug, image=sub_read.image,
        status=next_status, sortOrder=sub_read.sortOrder,
    )
    sub_category_service.update_sub_category(db, sub_category_id, update_payload)
    updated = sub_category_service.to_read(db, sub_category_service.get_sub_category(db, sub_category_id))
    parent = category_service.get_category(db, updated.categoryId)
    label = "Active" if next_status == "active" else "Inactive"
    return templates.TemplateResponse(
        "admin/partials/sub_category_row.html",
        {"request": request, "sub": updated, "parent_category": parent},
        headers=toast_only(f"Sub category marked {label}", toast_id="subCategoryToast"),
    )


# ======================================================================
# image upload (used inside the add/edit form)
# ======================================================================

@router.post("/upload-image", response_class=HTMLResponse)
async def sub_category_upload_image(request: Request, file: UploadFile = File(...)):
    try:
        url = await save_upload(file, "categories", allowed_extensions=IMAGE_EXTENSIONS, max_size_mb=2)
        return templates.TemplateResponse(
            "admin/partials/sub_category_image_preview.html",
            {"request": request, "image_url": url, "error": None},
        )
    except Exception as exc:
        detail = getattr(exc, "detail", "Could not upload image")
        return templates.TemplateResponse(
            "admin/partials/sub_category_image_preview.html",
            {"request": request, "image_url": None, "error": detail},
            status_code=status.HTTP_200_OK,
        )