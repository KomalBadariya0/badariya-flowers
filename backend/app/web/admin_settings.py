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
    POST /account              update login email / password. If the
                                email is being changed, this does NOT
                                save it yet -- it emails an OTP to the
                                NEW address and re-renders the Account
                                tab in an "enter code" state instead.
                                (Password-only changes, with no email
                                change, still save immediately.)
    POST /account/verify-otp   checks the code; only on success is the
                                pending email (+ password, if changed
                                together) actually written to the DB.
    POST /account/resend-otp   re-sends a fresh code to the same
                                pending new email (rate-limited).
    POST /account/cancel-otp   drops the pending change, back to the
                                normal Account form.
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
from app.services import auth_service, settings_service
from app.core.security import hash_password, verify_password
from app.utils.file_upload import FAVICON_EXTENSIONS, IMAGE_EXTENSIONS, save_upload
from app.web.deps import get_logged_in_admin_id, require_login, templates, toast_only

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
# shared render helper (settings tabs + Account tab)
# ======================================================================

def _render_settings_form(
    request: Request, db: Session, *,
    errors=None, form_values=None, account_errors=None, account_values=None,
    headers=None,
    account_otp_pending=False, account_otp_email=None, resend_cooldown=0,
) -> HTMLResponse:
    """Every branch of settings_save / settings_account_save re-renders the
    same full form fragment (site-settings tabs + the Account tab). This
    centralizes fetching the current admin (needed by the Account tab's
    email field) so each branch only needs to pass whichever errors are
    relevant to it.

    account_otp_pending flips the Account tab into "enter the code we
    just emailed you" mode instead of the normal email/password fields
    -- used while an email change is awaiting OTP confirmation."""
    row = settings_service.get_or_create(db)
    admin_id = get_logged_in_admin_id(request)
    admin = auth_service.get_admin_by_id(db, admin_id) if admin_id else None
    context = {
        "request": request,
        "s": settings_service.to_read(row),
        "errors": errors or {},
        "form_values": form_values,
        "admin": admin,
        "account_errors": account_errors or {},
        "account_values": account_values,
        "account_otp_pending": account_otp_pending,
        "account_otp_email": account_otp_email,
        "resend_cooldown": resend_cooldown,
    }
    return templates.TemplateResponse("admin/partials/settings_form.html", context, headers=headers)


def _pending_email_change(request: Request) -> dict | None:
    """The email-change OTP flow needs to remember, between the "send
    code" request and the "verify code" request, which new email is
    being confirmed (and the already-hashed new password, if one was
    submitted alongside it). The admin session is the right place for
    this -- it's already trusted, server-side, and tied to this one
    logged-in admin, so nothing sensitive ever round-trips through the
    browser as a hidden form field."""
    return request.session.get("pending_email_change")


# ======================================================================
# full page
# ======================================================================

@router.get("", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)):
    row = settings_service.get_or_create(db)
    data = settings_service.to_read(row)
    admin_id = get_logged_in_admin_id(request)
    admin = auth_service.get_admin_by_id(db, admin_id) if admin_id else None
    return templates.TemplateResponse(
        "admin/settings.html",
        {
            "request": request, "active_page": "settings", "s": data,
            "errors": {}, "form_values": None,
            "admin": admin, "account_errors": {}, "account_values": None,
        },
    )


# ======================================================================
# save
# ======================================================================

@router.post("", response_class=HTMLResponse)
async def settings_save(request: Request, db: Session = Depends(get_db)):
    payload, errors, form_values = await _build_payload_or_errors(request)
    if errors:
        return _render_settings_form(request, db, errors=errors, form_values=form_values)

    try:
        settings_service.update_settings(db, payload)
    except HTTPException as exc:
        db.rollback()
        return _render_settings_form(
            request, db, errors={_error_field(exc.detail): exc.detail}, form_values=form_values,
        )
    except SQLAlchemyError:
        db.rollback()
        return _render_settings_form(
            request, db,
            errors={"websiteName": "We couldn't save settings right now. Please try again."},
            form_values=form_values,
        )
    except Exception:  # anything unexpected — never let a raw error/traceback reach the user
        db.rollback()
        return _render_settings_form(
            request, db,
            errors={"websiteName": "Something went wrong while saving settings. Please try again."},
            form_values=form_values,
        )

    return _render_settings_form(
        request, db, headers=toast_only("Settings saved successfully", toast_id="settingsToast"),
    )


# ======================================================================
# account (email / password)
# ======================================================================

@router.post("/account", response_class=HTMLResponse)
async def settings_account_save(request: Request, db: Session = Depends(get_db)):
    admin_id = get_logged_in_admin_id(request)
    admin = auth_service.get_admin_by_id(db, admin_id) if admin_id else None
    if not admin:
        return _render_settings_form(request, db, account_errors={"currentPassword": "Your session expired — please log in again."})

    form = await request.form()
    current_password = form.get("currentPassword") or ""
    new_email = (form.get("newEmail") or "").strip().lower()
    new_password = form.get("newPassword") or ""
    confirm_password = form.get("confirmPassword") or ""

    errors: dict = {}

    if not current_password:
        errors["currentPassword"] = "Enter your current password to make changes"
    elif not verify_password(current_password, admin.password_hash):
        errors["currentPassword"] = "Current password is incorrect"

    if not new_email:
        errors["newEmail"] = "Email is required"
    elif new_email != admin.email:
        existing = auth_service.get_admin_by_email(db, new_email)
        if existing and existing.id != admin.id:
            errors["newEmail"] = "This email is already in use"

    wants_password_change = bool(new_password or confirm_password)
    if wants_password_change:
        if len(new_password) < 8:
            errors["newPassword"] = "Password must be at least 8 characters"
        elif new_password != confirm_password:
            errors["confirmPassword"] = "Passwords do not match"

    if errors:
        return _render_settings_form(
            request, db, account_errors=errors, account_values={"newEmail": new_email},
        )

    email_changing = new_email != admin.email

    if not email_changing:
        # No email change -> nothing to verify, save (password, if any)
        # immediately, exactly as before.
        if wants_password_change:
            admin.password_hash = hash_password(new_password)
            db.commit()
            db.refresh(admin)
        return _render_settings_form(
            request, db, headers=toast_only("Account updated successfully", toast_id="settingsToast"),
        )

    # Email is changing -> don't save it yet. Stash the pending new email
    # (+ already-hashed new password, if one was submitted alongside it)
    # in the session, email an OTP to the NEW address, and flip the
    # Account tab into "enter the code" mode instead.
    request.session["pending_email_change"] = {
        "admin_id": admin.id,
        "new_email": new_email,
        "new_password_hash": hash_password(new_password) if wants_password_change else None,
    }

    try:
        auth_service.create_and_send_email_change_otp(db, admin, new_email)
    except Exception:
        request.session.pop("pending_email_change", None)
        return _render_settings_form(
            request, db,
            account_errors={"newEmail": "Couldn't send the verification code. Please try again."},
            account_values={"newEmail": new_email},
        )

    cooldown = auth_service.seconds_until_resend_allowed(db, admin.id)
    return _render_settings_form(
        request, db, account_otp_pending=True, account_otp_email=new_email, resend_cooldown=cooldown,
    )


@router.post("/account/verify-otp", response_class=HTMLResponse)
async def settings_account_verify_otp(request: Request, db: Session = Depends(get_db)):
    admin_id = get_logged_in_admin_id(request)
    admin = auth_service.get_admin_by_id(db, admin_id) if admin_id else None
    pending = _pending_email_change(request)

    if not admin or not pending or pending.get("admin_id") != admin.id:
        request.session.pop("pending_email_change", None)
        return _render_settings_form(
            request, db, account_errors={"newEmail": "That email change has expired. Please try again."},
        )

    form = await request.form()
    otp = form.get("otp") or ""

    success, error = auth_service.verify_otp(db, admin.id, otp)
    if not success:
        cooldown = auth_service.seconds_until_resend_allowed(db, admin.id)
        return _render_settings_form(
            request, db,
            account_errors={"otp": error},
            account_otp_pending=True, account_otp_email=pending["new_email"], resend_cooldown=cooldown,
        )

    admin.email = pending["new_email"]
    if pending.get("new_password_hash"):
        admin.password_hash = pending["new_password_hash"]
    db.commit()
    db.refresh(admin)

    request.session.pop("pending_email_change", None)
    if request.session.get("admin_id") == admin.id:
        request.session["admin_email"] = admin.email

    return _render_settings_form(
        request, db, headers=toast_only("Email updated successfully", toast_id="settingsToast"),
    )


@router.post("/account/resend-otp", response_class=HTMLResponse)
async def settings_account_resend_otp(request: Request, db: Session = Depends(get_db)):
    admin_id = get_logged_in_admin_id(request)
    admin = auth_service.get_admin_by_id(db, admin_id) if admin_id else None
    pending = _pending_email_change(request)

    if not admin or not pending or pending.get("admin_id") != admin.id:
        request.session.pop("pending_email_change", None)
        return _render_settings_form(
            request, db, account_errors={"newEmail": "That email change has expired. Please try again."},
        )

    cooldown = auth_service.seconds_until_resend_allowed(db, admin.id)
    if cooldown <= 0:
        try:
            auth_service.create_and_send_email_change_otp(db, admin, pending["new_email"])
        except Exception:
            return _render_settings_form(
                request, db,
                account_errors={"otp": "Couldn't resend the code right now. Please try again shortly."},
                account_otp_pending=True, account_otp_email=pending["new_email"], resend_cooldown=0,
            )
        cooldown = auth_service.seconds_until_resend_allowed(db, admin.id)

    return _render_settings_form(
        request, db, account_otp_pending=True, account_otp_email=pending["new_email"], resend_cooldown=cooldown,
    )


@router.post("/account/cancel-otp", response_class=HTMLResponse)
async def settings_account_cancel_otp(request: Request, db: Session = Depends(get_db)):
    request.session.pop("pending_email_change", None)
    return _render_settings_form(request, db)


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