"""
Admin authentication — session-based login/logout.

Route map:
    GET  /admin           -> redirect to /admin/dashboard (if logged in)
                              or /admin/login (if not)
    GET  /admin/login      full login page (redirects to dashboard if
                            already logged in)
    POST /admin/login      validates credentials, sets the session, and
                            redirects to /admin/dashboard (or ?next=)
    GET  /admin/logout     destroys the session, redirects to /admin/login

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

    # Regenerate session state on login (avoids session fixation) and
    # remember the admin — the session cookie persists across browser
    # refreshes/restarts until logout (see SESSION_MAX_AGE in config.py).
    request.session.clear()
    request.session["admin_id"] = admin.id
    request.session["admin_email"] = admin.email
    request.session["admin_name"] = admin.name

    return RedirectResponse(_safe_next_url(next), status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=status.HTTP_303_SEE_OTHER)
