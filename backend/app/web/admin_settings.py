"""
Admin > Settings — server-rendered page + HTMX fragment endpoints.

Same architecture as Categories / Sub Categories / Products: FastAPI +
Jinja2 + HTMX, no fetch(), no JSON API round-trip from the browser. The
JSON API at /api/settings (app/api/settings.py) is untouched and keeps
working independently — this module only adds the admin-panel page.

Route map (all under /admin/settings):
    GET  ""                    full page (tabs + form, one Save button)
    POST ""                    save -> re-renders the form fragment with
                                either field errors or a success toast
    POST /upload-logo          image upload -> preview fragment (used
    POST /upload-favicon       inside the form; each renders a small
    POST /upload-hero-image    inline preview + an out-of-band swap of
    POST /upload-og-image      the hidden input that actually gets
                                submitted with the rest of the form)
"""
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.settings import SettingsUpdate
from app.services import settings_service
from app.utils.file_upload import FAVICON_EXTENSIONS, IMAGE_EXTENSIONS, save_upload
from app.web.deps import require_login, templates, toast_only

router = APIRouter(prefix="/admin/settings", tags=["Admin · Settings"], dependencies=[Depends(require_login)])


# ======================================================================
# helpers
# ======================================================================

# Inline templates for the four image-upload previews — kept as small
# render-from-string fragments (rather than new .html files) since they
# are only ever used by these four upload endpoints. Mirrors exactly the
# two-part response Categories uses for its image upload: the visible
# preview swap plus an out-of-band update of the hidden field that holds
# the real value submitted with the rest of the form.
_IMAGE_PREVIEW_INNER = """
{% if image_url %}
<img src="{{ image_url }}" alt="{{ label }} preview">
{% else %}
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="M21 16l-5.5-5.5L4 21"/></svg>
{% endif %}
{% if error %}
<span class="set-field-error" style="display:block;">{{ error }}</span>
{% endif %}
"""

_IMAGE_PREVIEW_RESPONSE = _IMAGE_PREVIEW_INNER + """
<input type="hidden" id="{{ hidden_id }}" name="{{ field_name }}" value="{{ image_url or '' }}" hx-swap-oob="true">
"""


def _render_image_preview(label: str, hidden_id: str, field_name: str, image_url, error=None) -> HTMLResponse:
    html = templates.env.from_string(_IMAGE_PREVIEW_RESPONSE).render(
        label=label, hidden_id=hidden_id, field_name=field_name, image_url=image_url, error=error,
    )
    return HTMLResponse(html)


async def _handle_image_upload(
    file: UploadFile, label: str, hidden_id: str, field_name: str, allowed_extensions, max_size_mb=None,
) -> HTMLResponse:
    try:
        url = await save_upload(file, "settings", allowed_extensions=allowed_extensions, max_size_mb=max_size_mb)
    except HTTPException as exc:
        return _render_image_preview(label, hidden_id, field_name, None, error=exc.detail)
    except Exception:
        return _render_image_preview(label, hidden_id, field_name, None, error="Upload failed. Please try again.")
    return _render_image_preview(label, hidden_id, field_name, url)


def _field_errors_from_validation_error(exc: ValidationError) -> dict:
    errors = {}
    for err in exc.errors():
        field = err["loc"][0] if err.get("loc") else "websiteName"
        errors[field] = err["msg"].replace("Value error, ", "")
    return errors


def _error_field(detail: str) -> str:
    text = str(detail).lower()
    if "email" in text:
        return "supportEmail" if "support" in text else "businessEmail"
    if "website name" in text or "name" in text:
        return "websiteName"
    return "websiteName"


async def _build_payload_or_errors(request: Request):
    form = await request.form()

    def val(name: str):
        v = form.get(name)
        return v if v not in (None, "") else None

    field_values = {
        "websiteName": form.get("websiteName", ""),
        "tagline": form.get("tagline", ""),
        "logo": form.get("logo", ""),
        "favicon": form.get("favicon", ""),
        "websiteStatus": form.get("websiteStatus", "active"),
        "maintenanceMode": form.get("maintenanceMode") == "on",
        "businessEmail": form.get("businessEmail", ""),
        "mobileNumber": form.get("mobileNumber", ""),
        "whatsappNumber": form.get("whatsappNumber", ""),
        "address": form.get("address", ""),
        "city": form.get("city", ""),
        "state": form.get("state", ""),
        "country": form.get("country", ""),
        "pincode": form.get("pincode", ""),
        "mapLink": form.get("mapLink", ""),
        "googleMapsEmbed": form.get("googleMapsEmbed", ""),
        "businessHours": form.get("businessHours", ""),
        "facebook": form.get("facebook", ""),
        "instagram": form.get("instagram", ""),
        "youtube": form.get("youtube", ""),
        "twitter": form.get("twitter", ""),
        "pinterest": form.get("pinterest", ""),
        "footerCopyright": form.get("footerCopyright", ""),
        "metaTitle": form.get("metaTitle", ""),
        "metaDescription": form.get("metaDescription", ""),
        "metaKeywords": form.get("metaKeywords", ""),
        "ogImage": form.get("ogImage", ""),
        "googleAnalyticsId": form.get("googleAnalyticsId", ""),
        "facebookPixelId": form.get("facebookPixelId", ""),
        "robotsTxt": form.get("robotsTxt", "index, follow"),
        "canonicalUrl": form.get("canonicalUrl", ""),
        "heroTitle": form.get("heroTitle", ""),
        "heroSubtitle": form.get("heroSubtitle", ""),
        "heroButtonText": form.get("heroButtonText", ""),
        "heroButtonLink": form.get("heroButtonLink", ""),
        "heroBgImage": form.get("heroBgImage", ""),
        "supportEmail": form.get("supportEmail", ""),
        "supportPhone": form.get("supportPhone", ""),
        "currency": form.get("currency", "INR"),
        "language": form.get("language", "en"),
        "productsPerPage": form.get("productsPerPage", "12"),
        "defaultWaMessage": form.get("defaultWaMessage", ""),
    }

    products_per_page_raw = field_values["productsPerPage"]
    try:
        products_per_page_value = int(products_per_page_raw) if str(products_per_page_raw).strip() else 12
    except ValueError:
        return None, {"productsPerPage": "Please enter a valid number"}, field_values

    try:
        payload = SettingsUpdate(
            websiteName=field_values["websiteName"],
            tagline=val("tagline"),
            logo=val("logo"),
            favicon=val("favicon"),
            websiteStatus=field_values["websiteStatus"],
            maintenanceMode=field_values["maintenanceMode"],
            businessEmail=val("businessEmail"),
            mobileNumber=val("mobileNumber"),
            whatsappNumber=val("whatsappNumber"),
            address=val("address"),
            city=val("city"),
            state=val("state"),
            country=val("country"),
            pincode=val("pincode"),
            mapLink=val("mapLink"),
            googleMapsEmbed=val("googleMapsEmbed"),
            businessHours=val("businessHours"),
            facebook=val("facebook"),
            instagram=val("instagram"),
            youtube=val("youtube"),
            twitter=val("twitter"),
            pinterest=val("pinterest"),
            footerCopyright=val("footerCopyright"),
            metaTitle=val("metaTitle"),
            metaDescription=val("metaDescription"),
            metaKeywords=val("metaKeywords"),
            ogImage=val("ogImage"),
            googleAnalyticsId=val("googleAnalyticsId"),
            facebookPixelId=val("facebookPixelId"),
            robotsTxt=field_values["robotsTxt"],
            canonicalUrl=val("canonicalUrl"),
            heroTitle=val("heroTitle"),
            heroSubtitle=val("heroSubtitle"),
            heroButtonText=val("heroButtonText"),
            heroButtonLink=val("heroButtonLink"),
            heroBgImage=val("heroBgImage"),
            supportEmail=val("supportEmail"),
            supportPhone=val("supportPhone"),
            currency=field_values["currency"],
            language=field_values["language"],
            productsPerPage=products_per_page_value,
            defaultWaMessage=val("defaultWaMessage"),
        )
        return payload, {}, field_values
    except ValidationError as exc:
        return None, _field_errors_from_validation_error(exc), field_values


# ======================================================================
# full page
# ======================================================================

@router.get("", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)):
    row = settings_service.get_or_create(db)
    data = settings_service.to_read(row)
    return templates.TemplateResponse(
        "admin/settings.html",
        {"request": request, "active_page": "settings", "s": data, "errors": {}, "form_values": None},
    )


# ======================================================================
# save
# ======================================================================

@router.post("", response_class=HTMLResponse)
async def settings_save(request: Request, db: Session = Depends(get_db)):
    payload, errors, form_values = await _build_payload_or_errors(request)
    if errors:
        row = settings_service.get_or_create(db)
        return templates.TemplateResponse(
            "admin/partials/settings_form.html",
            {"request": request, "s": settings_service.to_read(row), "errors": errors, "form_values": form_values},
        )

    try:
        settings_service.update_settings(db, payload)
    except HTTPException as exc:
        db.rollback()
        row = settings_service.get_or_create(db)
        return templates.TemplateResponse(
            "admin/partials/settings_form.html",
            {
                "request": request, "s": settings_service.to_read(row),
                "errors": {_error_field(exc.detail): exc.detail}, "form_values": form_values,
            },
        )
    except SQLAlchemyError:
        db.rollback()
        row = settings_service.get_or_create(db)
        return templates.TemplateResponse(
            "admin/partials/settings_form.html",
            {
                "request": request, "s": settings_service.to_read(row),
                "errors": {"websiteName": "We couldn't save settings right now. Please try again."},
                "form_values": form_values,
            },
        )
    except Exception:  # anything unexpected — never let a raw error/traceback reach the user
        db.rollback()
        row = settings_service.get_or_create(db)
        return templates.TemplateResponse(
            "admin/partials/settings_form.html",
            {
                "request": request, "s": settings_service.to_read(row),
                "errors": {"websiteName": "Something went wrong while saving settings. Please try again."},
                "form_values": form_values,
            },
        )

    row = settings_service.get_or_create(db)
    return templates.TemplateResponse(
        "admin/partials/settings_form.html",
        {"request": request, "s": settings_service.to_read(row), "errors": {}, "form_values": None},
        headers=toast_only("Settings saved successfully", toast_id="settingsToast"),
    )


# ======================================================================
# image uploads
# ======================================================================

@router.post("/upload-logo", response_class=HTMLResponse)
async def upload_logo(file: UploadFile = File(...)):
    return await _handle_image_upload(file, "Logo", "settingsLogoValue", "logo", IMAGE_EXTENSIONS, max_size_mb=2)


@router.post("/upload-favicon", response_class=HTMLResponse)
async def upload_favicon(file: UploadFile = File(...)):
    return await _handle_image_upload(
        file, "Favicon", "settingsFaviconValue", "favicon", FAVICON_EXTENSIONS, max_size_mb=0.5,
    )


@router.post("/upload-hero-image", response_class=HTMLResponse)
async def upload_hero_image(file: UploadFile = File(...)):
    return await _handle_image_upload(
        file, "Hero background", "settingsHeroBgValue", "heroBgImage", IMAGE_EXTENSIONS, max_size_mb=3,
    )


@router.post("/upload-og-image", response_class=HTMLResponse)
async def upload_og_image(file: UploadFile = File(...)):
    return await _handle_image_upload(
        file, "OG image", "settingsOgImageValue", "ogImage", IMAGE_EXTENSIONS, max_size_mb=2,
    )
