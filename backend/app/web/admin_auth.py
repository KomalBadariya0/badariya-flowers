"""
Admin authentication — session-based login/logout, with a mandatory
email OTP (2FA) step between password verification and dashboard access.

Route map:
    GET  /admin              -> redirect to /admin/dashboard (if logged in)
                                 or /admin/login (if not)
    GET  /admin/login         full login page (redirects to dashboard if
                               already logged in)
    POST /admin/login         validates email + password; on success does
                               NOT log the admin in yet — instead it
                               generates an OTP, emails it, stores a
                               *pending* (not yet authenticated) admin id
                               in the session, and redirects to
                               /admin/verify-otp
    GET  /admin/verify-otp    OTP entry page (only reachable mid-login)
    POST /admin/verify-otp    checks the OTP; only on success does the
                               real, authenticated session get created
                               and the admin is sent on to the dashboard
    GET  /admin/resend-otp    re-sends a fresh OTP (rate-limited)
    GET  /admin/logout        destroys the session, redirects to /admin/login

There is no public signup route by design — the only admin account is the
one created by the startup seed (see app/services/auth_service.py).
"""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette import status

from app.database.session import get_db
from app.services import auth_service
from app.web.deps import get_logged_in_admin_id, templates

router = APIRouter(tags=["Admin · Auth"])


def _safe_next_url(next_url: str | None) -> str:
    """Only ever redirect to a same-site /admin/... path — never follow an
    open-redirect-style absolute/external URL from the `next` param."""
    if next_url and next_url.startswith("/admin") and not next_url.startswith("//"):
        return next_url
    return "/admin/dashboard"


def _get_pending_admin_id(request: Request) -> int | None:
    return request.session.get("pending_admin_id")


@router.get("/admin")
def admin_root(request: Request):
    if get_logged_in_admin_id(request):
        return RedirectResponse("/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse("/admin/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/login")
def login_page(request: Request, next: str = "/admin/dashboard"):
    if get_logged_in_admin_id(request):
        return RedirectResponse(_safe_next_url(next), status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "next_url": next, "error": None, "email": None},
    )


@router.post("/admin/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/admin/dashboard"),
    db: Session = Depends(get_db),
):
    admin = auth_service.authenticate_admin(db, email, password)
    if not admin:
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "next_url": next,
                "error": "Invalid email or password. Please try again.",
                "email": email,
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Password is correct, but login is NOT complete yet — no admin_id is
    # set in the session at this point. Only a "pending" marker goes in,
    # which by itself grants no access to any /admin/* page.
    request.session.clear()
    request.session["pending_admin_id"] = admin.id
    request.session["pending_next"] = _safe_next_url(next)

    try:
        auth_service.create_and_send_otp(db, admin)
    except Exception:
        # Email didn't go out — don't strand the admin on a code-entry
        # page with no code coming. Send them back to try again.
        request.session.clear()
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "next_url": next,
                "error": "Couldn't send the verification code. Please try logging in again in a moment.",
                "email": email,
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return RedirectResponse("/admin/verify-otp", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/verify-otp")
def verify_otp_page(request: Request, db: Session = Depends(get_db)):
    pending_admin_id = _get_pending_admin_id(request)
    if not pending_admin_id:
        return RedirectResponse("/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    admin = auth_service.get_admin_by_id(db, pending_admin_id)
    if not admin or not admin.is_active:
        request.session.clear()
        return RedirectResponse("/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    cooldown = auth_service.seconds_until_resend_allowed(db, pending_admin_id)
    return templates.TemplateResponse(
        "admin/verify_otp.html",
        {
            "request": request,
            "email": admin.email,
            "error": None,
            "resend_cooldown": cooldown,
        },
    )


@router.post("/admin/verify-otp")
def verify_otp_submit(
    request: Request,
    otp: str = Form(...),
    db: Session = Depends(get_db),
):
    pending_admin_id = _get_pending_admin_id(request)
    if not pending_admin_id:
        return RedirectResponse("/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    admin = auth_service.get_admin_by_id(db, pending_admin_id)
    if not admin or not admin.is_active:
        request.session.clear()
        return RedirectResponse("/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    success, error = auth_service.verify_otp(db, pending_admin_id, otp)
    if not success:
        cooldown = auth_service.seconds_until_resend_allowed(db, pending_admin_id)
        return templates.TemplateResponse(
            "admin/verify_otp.html",
            {
                "request": request,
                "email": admin.email,
                "error": error,
                "resend_cooldown": cooldown,
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # OTP correct -> this is the moment the admin actually becomes logged
    # in. Regenerate session state (avoids session fixation) and drop the
    # pending markers.
    next_url = request.session.get("pending_next", "/admin/dashboard")
    request.session.clear()
    request.session["admin_id"] = admin.id
    request.session["admin_email"] = admin.email
    request.session["admin_name"] = admin.name

    return RedirectResponse(_safe_next_url(next_url), status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/resend-otp")
def resend_otp(request: Request, db: Session = Depends(get_db)):
    pending_admin_id = _get_pending_admin_id(request)
    if not pending_admin_id:
        return RedirectResponse("/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    admin = auth_service.get_admin_by_id(db, pending_admin_id)
    if not admin or not admin.is_active:
        request.session.clear()
        return RedirectResponse("/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    cooldown = auth_service.seconds_until_resend_allowed(db, pending_admin_id)
    if cooldown <= 0:
        try:
            auth_service.create_and_send_otp(db, admin)
        except Exception:
            return templates.TemplateResponse(
                "admin/verify_otp.html",
                {
                    "request": request,
                    "email": admin.email,
                    "error": "Couldn't resend the code right now. Please try again shortly.",
                    "resend_cooldown": 0,
                },
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    return RedirectResponse("/admin/verify-otp", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=status.HTTP_303_SEE_OTHER)