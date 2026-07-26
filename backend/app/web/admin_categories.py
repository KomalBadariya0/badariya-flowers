"""
Admin > Categories — server-rendered page + HTMX fragment endpoints.

Route map (all under /admin/categories):
    GET    ""                     full page (table + both modals, empty)
    GET    /rows                  <tbody> fragment — search / status filter
    GET    /new                   Add-Category form fragment (for the modal)
    GET    /{id}/edit             Edit-Category form fragment (prefilled)
    POST   ""                     create -> returns refreshed rows fragment
    PUT    /{id}                  update -> returns refreshed rows fragment
    DELETE /{id}                  delete -> returns refreshed rows fragment
    GET    /{id}/view             View-Category modal body fragment
    GET    /{id}/confirm-delete   Delete-confirm modal body fragment
    POST   /{id}/toggle-status    flips active/inactive -> single <tr> fragment
    POST   /upload-image          image upload -> preview fragment (used
                                   inside the Add/Edit form; the hidden
                                   input it renders is what actually gets
                                   submitted with the rest of the form)
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services import category_service
from app.utils.file_upload import IMAGE_EXTENSIONS, save_upload
from app.web.deps import require_login, retarget_header, templates, toast_and_close, toast_only

router = APIRouter(prefix="/admin/categories", tags=["Admin · Categories"], dependencies=[Depends(require_login)])


# ======================================================================
# helpers
# ======================================================================

def _rows_context(db: Session, search: Optional[str], status_filter: Optional[str]) -> dict:
    rows, total = category_service.list_categories(db, search=search, status_filter=status_filter)
    return {"rows": rows, "total": total}


def _field_errors_from_validation_error(exc: ValidationError) -> dict:
    errors = {}
    for err in exc.errors():
        field = err["loc"][-1]
        errors[field] = err["msg"]
    return errors


async def _build_payload_or_errors(
    name: str,
    slug: str,
    status_value: str,
    sort_order: str,
    image: Optional[str],
    schema_cls,
):
    """Runs the exact same CategoryCreate/CategoryUpdate pydantic
    validation the JSON API uses, from HTML form fields. Returns
    (payload, errors) — exactly one of which is not None/empty."""
    try:
        sort_order_int = int(sort_order) if str(sort_order).strip() else 1
    except ValueError:
        sort_order_int = 1
    try:
        payload = schema_cls(
            name=name,
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
def categories_page(request: Request, db: Session = Depends(get_db)):
    ctx = _rows_context(db, search=None, status_filter=None)
    return templates.TemplateResponse(
        "admin/categories.html",
        {"request": request, "active_page": "categories", **ctx},
    )


# ======================================================================
# table rows (search / status filter)
# ======================================================================

@router.get("/rows", response_class=HTMLResponse)
def categories_rows(
    request: Request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    ctx = _rows_context(db, search=search, status_filter=status)
    return templates.TemplateResponse(
        "admin/partials/category_rows.html", {"request": request, **ctx}
    )


# ======================================================================
# add / edit form fragments
# ======================================================================

@router.get("/new", response_class=HTMLResponse)
def category_form_new(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "admin/partials/category_form.html",
        {
            "request": request,
            "mode": "add",
            "category": None,
            "next_sort_order": category_service.next_sort_order(db),
            "errors": {},
        },
    )


@router.get("/{category_id}/edit", response_class=HTMLResponse)
def category_form_edit(category_id: int, request: Request, db: Session = Depends(get_db)):
    category = category_service.get_category(db, category_id)
    cat_read = category_service.to_read(db, category)
    return templates.TemplateResponse(
        "admin/partials/category_form.html",
        {
            "request": request,
            "mode": "edit",
            "category": cat_read,
            "next_sort_order": cat_read.sortOrder,
            "errors": {},
        },
    )


# ======================================================================
# create / update / delete
# ======================================================================

@router.post("", response_class=HTMLResponse)
async def category_create(
    request: Request,
    name: str = Form(""),
    slug: str = Form(""),
    status_value: str = Form("active", alias="status"),
    sortOrder: str = Form("1"),
    image: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    payload, errors = await _build_payload_or_errors(name, slug, status_value, sortOrder, image, CategoryCreate)
    form_values = {"name": name, "slug": slug, "status": status_value, "sortOrder": sortOrder, "image": image}
    if errors:
        return templates.TemplateResponse(
            "admin/partials/category_form.html",
            {"request": request, "mode": "add", "category": None, "next_sort_order": sortOrder,
             "errors": errors, "form_values": form_values},
            headers=retarget_header("#categoryForm"),
        )
    try:
        category_service.create_category(db, payload)
    except HTTPException as exc:  # duplicate name/slug -> HTTPException(400)
        field = "slug" if "slug" in str(exc.detail).lower() else "name"
        return templates.TemplateResponse(
            "admin/partials/category_form.html",
            {"request": request, "mode": "add", "category": None, "next_sort_order": sortOrder,
             "errors": {field: exc.detail}, "form_values": form_values},
            headers=retarget_header("#categoryForm"),
        )
    ctx = _rows_context(db, search=None, status_filter=None)
    return templates.TemplateResponse(
        "admin/partials/category_rows.html",
        {"request": request, **ctx},
        headers=toast_and_close("Category added successfully", "categoryFormModal"),
    )


@router.put("/{category_id}", response_class=HTMLResponse)
async def category_update(
    category_id: int,
    request: Request,
    name: str = Form(""),
    slug: str = Form(""),
    status_value: str = Form("active", alias="status"),
    sortOrder: str = Form("1"),
    image: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    payload, errors = await _build_payload_or_errors(name, slug, status_value, sortOrder, image, CategoryUpdate)
    form_values = {"name": name, "slug": slug, "status": status_value, "sortOrder": sortOrder, "image": image}
    if errors:
        existing = category_service.to_read(db, category_service.get_category(db, category_id))
        return templates.TemplateResponse(
            "admin/partials/category_form.html",
            {"request": request, "mode": "edit", "category": existing, "next_sort_order": sortOrder,
             "errors": errors, "form_values": form_values},
            headers=retarget_header("#categoryForm"),
        )
    try:
        category_service.update_category(db, category_id, payload)
    except HTTPException as exc:
        field = "slug" if "slug" in str(exc.detail).lower() else "name"
        existing = category_service.to_read(db, category_service.get_category(db, category_id))
        return templates.TemplateResponse(
            "admin/partials/category_form.html",
            {"request": request, "mode": "edit", "category": existing, "next_sort_order": sortOrder,
             "errors": {field: exc.detail}, "form_values": form_values},
            headers=retarget_header("#categoryForm"),
        )
    ctx = _rows_context(db, search=None, status_filter=None)
    return templates.TemplateResponse(
        "admin/partials/category_rows.html",
        {"request": request, **ctx},
        headers=toast_and_close("Category updated successfully", "categoryFormModal"),
    )


@router.delete("/{category_id}", response_class=HTMLResponse)
def category_delete(category_id: int, request: Request, db: Session = Depends(get_db)):
    category_service.delete_category(db, category_id)
    ctx = _rows_context(db, search=None, status_filter=None)
    return templates.TemplateResponse(
        "admin/partials/category_rows.html",
        {"request": request, **ctx},
        headers=toast_and_close("Category deleted", "categoryDeleteModal"),
    )


# ======================================================================
# view / delete-confirm fragments
# ======================================================================

@router.get("/{category_id}/view", response_class=HTMLResponse)
def category_view(category_id: int, request: Request, db: Session = Depends(get_db)):
    category = category_service.get_category(db, category_id)
    cat_read = category_service.to_read(db, category)
    return templates.TemplateResponse(
        "admin/partials/category_view.html", {"request": request, "category": cat_read}
    )


@router.get("/{category_id}/confirm-delete", response_class=HTMLResponse)
def category_confirm_delete(category_id: int, request: Request, db: Session = Depends(get_db)):
    category = category_service.get_category(db, category_id)
    cat_read = category_service.to_read(db, category)
    return templates.TemplateResponse(
        "admin/partials/category_delete_confirm.html", {"request": request, "category": cat_read}
    )


# ======================================================================
# toggle status (single row swap)
# ======================================================================

@router.post("/{category_id}/toggle-status", response_class=HTMLResponse)
def category_toggle_status(category_id: int, request: Request, db: Session = Depends(get_db)):
    category = category_service.get_category(db, category_id)
    cat_read = category_service.to_read(db, category)
    next_status = "inactive" if cat_read.status == "active" else "active"
    update_payload = CategoryUpdate(
        name=cat_read.name, slug=cat_read.slug, image=cat_read.image,
        status=next_status, sortOrder=cat_read.sortOrder,
    )
    category_service.update_category(db, category_id, update_payload)
    updated = category_service.to_read(db, category_service.get_category(db, category_id))
    label = "Active" if next_status == "active" else "Inactive"
    return templates.TemplateResponse(
        "admin/partials/category_row.html",
        {"request": request, "cat": updated},
        headers=toast_only(f"Category marked {label}"),
    )


# ======================================================================
# image upload (used inside the add/edit form)
# ======================================================================

@router.post("/upload-image", response_class=HTMLResponse)
async def category_upload_image(request: Request, file: UploadFile = File(...)):
    try:
        url = await save_upload(file, "categories", allowed_extensions=IMAGE_EXTENSIONS, max_size_mb=2)
        return templates.TemplateResponse(
            "admin/partials/category_image_preview.html",
            {"request": request, "image_url": url, "error": None},
        )
    except Exception as exc:
        detail = getattr(exc, "detail", "Could not upload image")
        return templates.TemplateResponse(
            "admin/partials/category_image_preview.html",
            {"request": request, "image_url": None, "error": detail},
            status_code=status.HTTP_200_OK,  # 200 so HTMX still swaps in the error message
        )
