"""
Admin > Products — server-rendered pages + HTMX fragment endpoints.

Mirrors app/web/admin_categories.py and app/web/admin_sub_categories.py:
same HX-Trigger toast/close conventions, same "reuse the service layer,
don't touch it" rule. All business logic / validation / DB access is
delegated to the existing app.services.product_service (unchanged) —
category_service and sub_category_service are reused only to populate
the Category / Sub Category dropdowns, exactly like admin_sub_categories
reuses category_service for its parent dropdown.

Two differences from Categories / Sub Categories, both driven by the
*existing* (pre-HTMX) admin UI this migrates, not by a new design:

1. Add/Edit are dedicated pages (GET /admin/products/new,
   GET /admin/products/{id}/edit) instead of a modal — this matches
   admin/product-add.html, which was always its own page with tabs
   (Basic Info / Images / Details / SEO), not a modal, because the form
   has far more fields than Category/Sub Category. On success they
   HX-Redirect back to the listing page (same end result as the old
   `window.location = "products.html"` in product-form.js).

2. Product images are a list, not a single field. This router follows
   the same two-step pattern product_service already exposes for the
   JSON API: images are pre-uploaded (POST /upload-images -> URLs),
   held as hidden `images` form fields in the gallery grid, and the
   full ordered list is resubmitted on every create/update — mirrors
   ProductService._sync_images(), which always replaces the full set.
   No new per-image attach/detach logic is introduced here.

Route map (all under /admin/products):
    GET    ""                        full listing page (table + view/delete modals)
    GET    /rows                     <tbody> fragment — search / category / sub-category / status / featured filters
    GET    /new                      Add Product page (own layout, tabs)
    GET    /{id}/edit                Edit Product page (prefilled)
    POST   ""                        create -> HX-Redirect to /admin/products
    PUT    /{id}                     update -> HX-Redirect to /admin/products
    DELETE /{id}                     delete -> refreshed rows fragment
    GET    /{id}/view                View-Product modal body fragment
    GET    /{id}/confirm-delete      Delete-confirm modal body fragment
    POST   /{id}/toggle-status       flips active/inactive -> single <tr> fragment
    GET    /subcategory-options      <option> fragment for the Sub Category dropdown, filtered by categoryId
    POST   /upload-images            gallery multi-image upload -> appended gallery-item fragment(s)
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.product import ProductCreate, ProductUpdate, SeoInfo, SpecificationItem
from app.services import category_service, product_service, sub_category_service
from app.utils.file_upload import IMAGE_EXTENSIONS, save_upload
from app.web.deps import hx_trigger_header, require_login, retarget_header, templates, toast_and_close, toast_only

router = APIRouter(prefix="/admin/products", tags=["Admin · Products"], dependencies=[Depends(require_login)])


# ======================================================================
# helpers
# ======================================================================

def _category_options(db: Session):
    """All categories, for the Category <select> — reuses the exact same
    service function app.web.admin_categories / admin_sub_categories rely on."""
    rows, _ = category_service.list_categories(db)
    return rows


def _sub_category_options(db: Session, category_id: Optional[int]):
    """Sub categories for the (optionally category-scoped) Sub Category
    <select> — reuses sub_category_service, same as the JSON API's
    GET /products/meta/subcategories."""
    rows, _ = sub_category_service.list_sub_categories(db, category_id=category_id)
    return rows


PAGE_SIZE = 8


def _rows_context(
    db: Session,
    search: Optional[str],
    category_id: Optional[int],
    sub_category_id: Optional[int],
    status_filter: Optional[str],
    featured: Optional[bool],
    page: int = 1,
) -> dict:
    rows, total = product_service.list_products(
        db, search=search, category_id=category_id, sub_category_id=sub_category_id,
        status_filter=status_filter, featured=featured,
    )
    total_pages = max(1, -(-total // PAGE_SIZE))  # ceil division
    page = max(1, min(page, total_pages))
    start = (page - 1) * PAGE_SIZE
    page_rows = rows[start:start + PAGE_SIZE]
    categories = _category_options(db)
    cat_by_id = {c.id: c.name for c in categories}
    sub_by_id = {}
    if page_rows:
        all_subs, _ = sub_category_service.list_sub_categories(db)
        sub_by_id = {s.id: s.name for s in all_subs}
    return {
        "rows": page_rows,
        "total": total,
        "categories": categories,
        "cat_by_id": cat_by_id,
        "sub_by_id": sub_by_id,
        "page": page,
        "total_pages": total_pages,
    }


def _sub_category_name(db: Session, sub_category_id: Optional[int]) -> Optional[str]:
    if not sub_category_id:
        return None
    try:
        sub = sub_category_service.get_sub_category(db, sub_category_id)
        return sub.name
    except Exception:
        return None


def _field_errors_from_validation_error(exc: ValidationError) -> dict:
    errors = {}
    for err in exc.errors():
        field = err["loc"][-1]
        errors[str(field)] = err["msg"]
    return errors


def _parse_bool(value: Optional[str]) -> bool:
    return str(value).lower() in ("on", "true", "1", "yes")


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None or not str(value).strip():
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_int(value: Optional[str], default: int = 1) -> int:
    try:
        return int(value) if str(value).strip() else default
    except ValueError:
        return default


def _error_field(detail: str) -> str:
    """Best-effort mapping of a service-layer error message to the form
    field it should be shown under — mirrors admin_categories.py's
    slug/name detection, extended with the fields Products has that
    Categories doesn't."""
    text = str(detail).lower()
    if "sku" in text:
        return "sku"
    if "sub category" in text:
        return "subCategoryId"
    if "price" in text:
        return "price"
    return "name"


async def _build_payload_or_errors(request: Request, schema_cls):
    """Runs the exact same ProductCreate/ProductUpdate pydantic validation
    the JSON API uses, from HTML form fields — including the repeated
    fields (tags[], images[], specLabel[]/specValue[], features[]) that
    don't fit a flat FastAPI Form(...) signature, so the raw form is read
    directly instead."""
    form = await request.form()

    tags = [t.strip() for t in form.getlist("tags") if t.strip()]
    images = [u for u in form.getlist("images") if u]
    features = [f.strip() for f in form.getlist("features") if f.strip()]

    spec_labels = form.getlist("specLabel")
    spec_values = form.getlist("specValue")
    specifications = [
        {"label": label.strip(), "value": value.strip()}
        for label, value in zip(spec_labels, spec_values)
        if label.strip() and value.strip()
    ]

    category_id_raw = form.get("categoryId", "")
    sub_category_id_raw = form.get("subCategoryId", "")
    price_raw = form.get("price", "")

    field_values = {
        "name": form.get("name", ""),
        "categoryId": category_id_raw,
        "subCategoryId": sub_category_id_raw,
        "sku": form.get("sku") or None,
        "price": price_raw,
        "priceNote": form.get("priceNote") or None,
        "moq": form.get("moq", "1"),
        "shortDesc": form.get("shortDesc") or None,
        "fullDesc": form.get("fullDesc") or None,
        "material": form.get("material") or None,
        "color": form.get("color") or None,
        "weight": form.get("weight") or None,
        "dimensions": form.get("dimensions") or None,
        "tags": tags,
        "images": images,
        "featured": _parse_bool(form.get("featured")),
        "active": _parse_bool(form.get("active")),
        "usage": form.get("usage") or None,
        "careInstructions": form.get("careInstructions") or None,
        "seoTitle": form.get("seoTitle") or None,
        "seoDesc": form.get("seoDesc") or None,
        "seoKeywords": form.get("seoKeywords") or None,
        "seoSlug": form.get("seoSlug") or None,
    }

    manual_errors = {}

    price_value: Optional[float] = None
    if price_raw and price_raw.strip():
        try:
            price_value = float(price_raw)
            if price_value < 0:
                manual_errors["price"] = "Price must be greater than zero"
        except ValueError:
            manual_errors["price"] = "Please enter a valid price"

    category_id_value: Optional[int] = None
    if str(category_id_raw).strip():
        try:
            category_id_value = int(category_id_raw)
        except ValueError:
            manual_errors["categoryId"] = "Please select a valid category"

    sub_category_id_value = 0
    if str(sub_category_id_raw).strip():
        try:
            sub_category_id_value = int(sub_category_id_raw)
        except ValueError:
            manual_errors["subCategoryId"] = "Please select a sub category"
    if not sub_category_id_value and "subCategoryId" not in manual_errors:
        manual_errors["subCategoryId"] = "Please select a sub category"

    if manual_errors:
        return None, manual_errors, field_values

    try:
        payload = schema_cls(
            name=field_values["name"],
            categoryId=category_id_value,
            subCategoryId=sub_category_id_value,
            sku=field_values["sku"],
            price=price_value,
            priceNote=field_values["priceNote"],
            moq=_parse_int(field_values["moq"], default=1),
            shortDesc=field_values["shortDesc"],
            fullDesc=field_values["fullDesc"],
            material=field_values["material"],
            color=field_values["color"],
            weight=field_values["weight"],
            dimensions=field_values["dimensions"],
            tags=tags,
            images=images,
            featured=field_values["featured"],
            active=field_values["active"],
            specifications=[SpecificationItem(**s) for s in specifications],
            features=features,
            usage=field_values["usage"],
            careInstructions=field_values["careInstructions"],
            seo=SeoInfo(
                title=field_values["seoTitle"],
                description=field_values["seoDesc"],
                keywords=field_values["seoKeywords"],
                slug=field_values["seoSlug"],
            ),
        )
        return payload, {}, field_values
    except ValidationError as exc:
        return None, _field_errors_from_validation_error(exc), field_values


# ======================================================================
# full listing page
# ======================================================================

@router.get("", response_class=HTMLResponse)
def products_page(request: Request, db: Session = Depends(get_db)):
    ctx = _rows_context(db, search=None, category_id=None, sub_category_id=None,
                         status_filter=None, featured=None)
    return templates.TemplateResponse(
        "admin/products.html",
        {"request": request, "active_page": "products", **ctx},
    )


# ======================================================================
# table rows (search / category / sub-category / status / featured filters)
# ======================================================================

@router.get("/rows", response_class=HTMLResponse)
def products_rows(
    request: Request,
    search: Optional[str] = None,
    categoryId: Optional[str] = None,
    subCategoryId: Optional[str] = None,
    status: Optional[str] = None,
    featured: Optional[str] = None,
    page: int = 1,
    db: Session = Depends(get_db),
):
    cat_id = int(categoryId) if categoryId and categoryId != "all" else None
    sub_id = int(subCategoryId) if subCategoryId and subCategoryId != "all" else None
    status_filter = status if status and status != "all" else None
    featured_filter = None
    if featured == "yes":
        featured_filter = True
    elif featured == "no":
        featured_filter = False
    ctx = _rows_context(db, search=search, category_id=cat_id, sub_category_id=sub_id,
                         status_filter=status_filter, featured=featured_filter, page=page)
    return templates.TemplateResponse("admin/partials/product_rows.html", {"request": request, **ctx})


# ======================================================================
# add / edit pages (dedicated pages, matching the existing product-add.html)
# ======================================================================

@router.get("/new", response_class=HTMLResponse)
def product_form_new(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "admin/product-form.html",
        {
            "request": request,
            "active_page": "products",
            "mode": "add",
            "product": None,
            "categories": _category_options(db),
            "sub_categories": [],
            "errors": {},
            "form_values": {},
        },
    )


@router.get("/{product_id}/edit", response_class=HTMLResponse)
def product_form_edit(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    product_read = product_service.to_read(product)
    return templates.TemplateResponse(
        "admin/product-form.html",
        {
            "request": request,
            "active_page": "products",
            "mode": "edit",
            "product": product_read,
            "categories": _category_options(db),
            "sub_categories": _sub_category_options(db, product_read.categoryId),
            "errors": {},
            "form_values": {},
        },
    )


# ======================================================================
# create / update / delete
# ======================================================================

@router.post("", response_class=HTMLResponse)
async def product_create(request: Request, db: Session = Depends(get_db)):
    payload, errors, form_values = await _build_payload_or_errors(request, ProductCreate)
    if errors:
        return templates.TemplateResponse(
            "admin/partials/product_form_fields.html",
            {
                "request": request, "mode": "add", "product": None,
                "categories": _category_options(db),
                "sub_categories": _sub_category_options(db, payload.categoryId if payload else None),
                "errors": errors, "form_values": form_values,
            },
        )
    try:
        product_service.create_product(db, payload)
    except HTTPException as exc:  # duplicate SKU / missing sub category -> friendly 400 from the service
        db.rollback()
        return templates.TemplateResponse(
            "admin/partials/product_form_fields.html",
            {
                "request": request, "mode": "add", "product": None,
                "categories": _category_options(db),
                "sub_categories": _sub_category_options(db, payload.categoryId),
                "errors": {_error_field(exc.detail): exc.detail}, "form_values": form_values,
            },
        )
    except Exception:  # anything unexpected — never let a raw error/traceback reach the user
        db.rollback()
        return templates.TemplateResponse(
            "admin/partials/product_form_fields.html",
            {
                "request": request, "mode": "add", "product": None,
                "categories": _category_options(db),
                "sub_categories": _sub_category_options(db, payload.categoryId),
                "errors": {"name": "Something went wrong while saving the product. Please try again."},
                "form_values": form_values,
            },
        )
    return HTMLResponse(
        content="",
        headers={
            "HX-Redirect": "/admin/products",
            **hx_trigger_header({"toast": {"message": "Product added successfully", "type": "success", "toastId": "productToast"}}),
        },
    )


@router.put("/{product_id}", response_class=HTMLResponse)
async def product_update(product_id: int, request: Request, db: Session = Depends(get_db)):
    payload, errors, form_values = await _build_payload_or_errors(request, ProductUpdate)
    if errors:
        existing = product_service.to_read(product_service.get_product(db, product_id))
        return templates.TemplateResponse(
            "admin/partials/product_form_fields.html",
            {
                "request": request, "mode": "edit", "product": existing,
                "categories": _category_options(db),
                "sub_categories": _sub_category_options(db, payload.categoryId if payload else existing.categoryId),
                "errors": errors, "form_values": form_values,
            },
        )
    try:
        product_service.update_product(db, product_id, payload)
    except HTTPException as exc:  # duplicate SKU / missing sub category -> friendly 400 from the service
        db.rollback()
        existing = product_service.to_read(product_service.get_product(db, product_id))
        return templates.TemplateResponse(
            "admin/partials/product_form_fields.html",
            {
                "request": request, "mode": "edit", "product": existing,
                "categories": _category_options(db),
                "sub_categories": _sub_category_options(db, payload.categoryId),
                "errors": {_error_field(exc.detail): exc.detail}, "form_values": form_values,
            },
        )
    except Exception:  # anything unexpected — never let a raw error/traceback reach the user
        db.rollback()
        existing = product_service.to_read(product_service.get_product(db, product_id))
        return templates.TemplateResponse(
            "admin/partials/product_form_fields.html",
            {
                "request": request, "mode": "edit", "product": existing,
                "categories": _category_options(db),
                "sub_categories": _sub_category_options(db, payload.categoryId),
                "errors": {"name": "Something went wrong while saving the product. Please try again."},
                "form_values": form_values,
            },
        )
    return HTMLResponse(
        content="",
        headers={
            "HX-Redirect": "/admin/products",
            **hx_trigger_header({"toast": {"message": "Product updated successfully", "type": "success", "toastId": "productToast"}}),
        },
    )


@router.delete("/{product_id}", response_class=HTMLResponse)
def product_delete(product_id: int, request: Request, db: Session = Depends(get_db)):
    product_service.delete_product(db, product_id)
    ctx = _rows_context(db, search=None, category_id=None, sub_category_id=None,
                         status_filter=None, featured=None)
    return templates.TemplateResponse(
        "admin/partials/product_rows.html",
        {"request": request, **ctx},
        headers=toast_and_close("Product deleted", "productDeleteModal", toast_id="productToast"),
    )


# ======================================================================
# view / delete-confirm fragments (used from the listing page)
# ======================================================================

@router.get("/{product_id}/view", response_class=HTMLResponse)
def product_view(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    product_read = product_service.to_read(product)
    parent_category = category_service.get_category(db, product_read.categoryId) if product_read.categoryId else None
    sub_category_name = _sub_category_name(db, product_read.subCategoryId)
    return templates.TemplateResponse(
        "admin/partials/product_view.html",
        {"request": request, "product": product_read, "parent_category": parent_category, "sub_category_name": sub_category_name},
    )


@router.get("/{product_id}/confirm-delete", response_class=HTMLResponse)
def product_confirm_delete(product_id: int, request: Request, db: Session = Depends(get_db)):
    product_read = product_service.to_read(product_service.get_product(db, product_id))
    return templates.TemplateResponse(
        "admin/partials/product_delete_confirm.html", {"request": request, "product": product_read}
    )


# ======================================================================
# toggle status (single row swap)
# ======================================================================

@router.post("/{product_id}/toggle-status", response_class=HTMLResponse)
def product_toggle_status(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    product_read = product_service.to_read(product)
    next_active = not product_read.active

    update_payload = ProductUpdate(
        name=product_read.name, categoryId=product_read.categoryId, subCategoryId=product_read.subCategoryId,
        sku=product_read.sku, price=product_read.price, priceNote=product_read.priceNote, moq=product_read.moq,
        shortDesc=product_read.shortDesc, fullDesc=product_read.fullDesc, material=product_read.material,
        color=product_read.color, weight=product_read.weight, dimensions=product_read.dimensions,
        tags=product_read.tags, images=product_read.images, featured=product_read.featured, active=next_active,
        specifications=product_read.specifications, features=product_read.features, usage=product_read.usage,
        careInstructions=product_read.careInstructions, seo=product_read.seo,
    )
    product_service.update_product(db, product_id, update_payload)
    updated = product_service.to_read(product_service.get_product(db, product_id))
    parent_category = category_service.get_category(db, updated.categoryId) if updated.categoryId else None
    sub_category_name = _sub_category_name(db, updated.subCategoryId)
    label = "Active" if next_active else "Inactive"
    return templates.TemplateResponse(
        "admin/partials/product_row.html",
        {"request": request, "p": updated, "parent_category": parent_category, "sub_category_name": sub_category_name},
        headers=toast_only(f"Product marked {label}", toast_id="productToast"),
    )


@router.post("/{product_id}/toggle-featured", response_class=HTMLResponse)
def product_toggle_featured(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    product_read = product_service.to_read(product)
    next_featured = not product_read.featured

    update_payload = ProductUpdate(
        name=product_read.name, categoryId=product_read.categoryId, subCategoryId=product_read.subCategoryId,
        sku=product_read.sku, price=product_read.price, priceNote=product_read.priceNote, moq=product_read.moq,
        shortDesc=product_read.shortDesc, fullDesc=product_read.fullDesc, material=product_read.material,
        color=product_read.color, weight=product_read.weight, dimensions=product_read.dimensions,
        tags=product_read.tags, images=product_read.images, featured=next_featured, active=product_read.active,
        specifications=product_read.specifications, features=product_read.features, usage=product_read.usage,
        careInstructions=product_read.careInstructions, seo=product_read.seo,
    )
    product_service.update_product(db, product_id, update_payload)
    updated = product_service.to_read(product_service.get_product(db, product_id))
    parent_category = category_service.get_category(db, updated.categoryId) if updated.categoryId else None
    sub_category_name = _sub_category_name(db, updated.subCategoryId)
    label = "marked as Featured" if next_featured else "removed from Featured"
    return templates.TemplateResponse(
        "admin/partials/product_row.html",
        {"request": request, "p": updated, "parent_category": parent_category, "sub_category_name": sub_category_name},
        headers=toast_only(f"Product {label}", toast_id="productToast"),
    )


# ======================================================================
# cascading Category -> Sub Category dropdown
# ======================================================================

@router.get("/subcategory-options", response_class=HTMLResponse)
def product_subcategory_options(
    request: Request, categoryId: Optional[str] = None, selectedSub: Optional[str] = None, db: Session = Depends(get_db)
):
    cat_id = int(categoryId) if categoryId and categoryId.strip() else None
    return templates.TemplateResponse(
        "admin/partials/product_subcategory_options.html",
        {"request": request, "sub_categories": _sub_category_options(db, cat_id), "selected_sub": selectedSub},
    )


# ======================================================================
# gallery image upload (used inside the add/edit form)
# ======================================================================

@router.post("/upload-images", response_class=HTMLResponse)
async def product_upload_images(request: Request, files: list[UploadFile] = File(...)):
    items = []
    for file in files:
        try:
            url = await save_upload(file, "products", allowed_extensions=IMAGE_EXTENSIONS, max_size_mb=2)
            items.append({"url": url, "error": None})
        except Exception as exc:
            items.append({"url": None, "error": getattr(exc, "detail", "Could not upload image")})
    return templates.TemplateResponse(
        "admin/partials/product_gallery_items.html",
        {"request": request, "items": items},
    )