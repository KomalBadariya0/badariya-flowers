"""
Shared dependencies for app.web routes: the Jinja2Templates instance and
small helpers for talking to HTMX on the response side (toasts, closing
a modal after a successful save/delete) via the HX-Trigger header.
"""
import json
from typing import Any, Optional

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.database.session import get_db
from app.services import auth_service

templates = Jinja2Templates(directory=str(settings.templates_dir))


# ======================================================================
# Admin login / session helpers
# ======================================================================

class RedirectException(Exception):
    """Raised by require_login (and anything else that needs to bounce the
    browser to another page) instead of an HTTPException, since a plain
    HTTPException on these HTML routes would otherwise be turned into a
    JSON error body by the app-wide exception handler in main.py. A
    dedicated handler in main.py turns this into a real redirect."""

    def __init__(self, url: str):
        self.url = url


def get_logged_in_admin_id(request: Request) -> Optional[int]:
    return request.session.get("admin_id")


async def require_login(request: Request):
    """Dependency for every protected /admin/* page. Include it as
    dependencies=[Depends(require_login)] on a router (or a single route)
    -- no return value is used, it either lets the request through or
    raises RedirectException("/admin/login")."""
    admin_id = get_logged_in_admin_id(request)
    if not admin_id:
        next_url = request.url.path
        raise RedirectException(f"/admin/login?next={next_url}")

    db = next(get_db())
    try:
        admin = auth_service.get_admin_by_id(db, admin_id)
        if not admin or not admin.is_active:
            request.session.clear()
            raise RedirectException("/admin/login")
    finally:
        db.close()

    return admin_id


def hx_trigger_header(events: dict) -> dict:
    """Builds the {'HX-Trigger': '...'} header dict HTMX reads to fire
    one or more client-side CustomEvents after a swap. `events` maps
    event name -> detail payload, e.g.:
        hx_trigger_header({
            "toast": {"message": "Category added", "type": "success"},
            "closeModal": {"id": "categoryFormModal"},
        })
    """
    return {"HX-Trigger": json.dumps(events)}


def toast_and_close(message: str, modal_id: str, type_: str = "success", toast_id: Optional[str] = None) -> dict:
    """Convenience wrapper for the very common case: show a toast AND
    close a modal in the same response.

    `toast_id` lets other modules (Sub Categories, Products, ...) target
    their own toast element instead of htmx-ui.js's default
    "categoryToast" fallback. Omitting it keeps the exact previous
    behaviour for Categories."""
    detail: dict[str, Any] = {"message": message, "type": type_}
    if toast_id:
        detail["toastId"] = toast_id
    return hx_trigger_header({
        "toast": detail,
        "closeModal": {"id": modal_id},
    })


def toast_only(message: str, type_: str = "success", toast_id: Optional[str] = None) -> dict:
    detail: dict[str, Any] = {"message": message, "type": type_}
    if toast_id:
        detail["toastId"] = toast_id
    return hx_trigger_header({"toast": detail})


def retarget_header(selector: str, swap: str = "innerHTML") -> dict:
    """On a validation/duplicate error, the Save button's own hx-target
    normally points at the table (for the success case). This header
    tells HTMX, for just this one response, to swap the form fragment
    back into the form instead — so inline field errors show up in the
    right place with zero client-side branching logic."""
    return {"HX-Retarget": selector, "HX-Reswap": swap}