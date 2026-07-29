"""
Badariya Flowers API — Application Entry Point
Run:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.api import (
    categories,
    sub_categories,
    products,
    catalogues,
    settings as settings_router,
    upload,
)

# Server-rendered (Jinja2 + HTMX) admin pages. Separate from app.api —
# these return HTML, app.api keeps returning JSON (unchanged, kept for
# backward compatibility per the migration plan).
from app.web import (
    admin_auth,
    admin_categories,
    admin_sub_categories,
    admin_products,
    admin_settings,
    admin_catalogue,
    admin_dashboard,
    site,
)
from app.web.deps import RedirectException

from app.core.config import settings
from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.services import auth_service

# Import all models so SQLAlchemy registers every table
from app.models import (
    category,
    sub_category,
    product,
    product_image,
    catalogue,
    settings as settings_model,
    admin_user,
    admin_otp,
)


# ======================================================
# FastAPI App
# ======================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Badariya Flowers",
)


# ======================================================
# Sessions (admin login)
# ======================================================

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_MAX_AGE,
)


# ======================================================
# CORS
# ======================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_origins_list != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================================================
# Static Uploads
# ======================================================

app.mount(
    "/uploads",
    StaticFiles(directory=str(settings.upload_root)),
    name="uploads",
)


# ======================================================
# Admin Web Routes (Jinja2 + HTMX) — must be included
# BEFORE the /admin static mount below, so an explicit
# route like /admin/categories or /admin/dashboard wins
# over the catch-all static mount for that exact path.
# ======================================================

app.include_router(admin_auth.router)
app.include_router(admin_dashboard.router)
app.include_router(admin_categories.router)
app.include_router(admin_sub_categories.router)
app.include_router(admin_products.router)
app.include_router(admin_settings.router)
app.include_router(admin_catalogue.router)


# ======================================================
# Public Website Routes
# ======================================================
# The customer-facing site (index.html, category.html, product.html,
# catalogue.html, cart.html, about.html, contact.html) is served through
# these routes at clean URLs — same app, same port. Must also be included
# before the static mounts below so e.g. GET / doesn't fall through to a
# 404 from the /assets mount.

app.include_router(site.router)


# ======================================================
# Frontend Static Assets
# ======================================================
# /assets  -> project-root/assets   (shared site design tokens, images,
#             fonts — used by both the customer site and every admin page)
# /admin   -> project-root/admin    (admin-only assets: admin.css,
#             are real routes registered above, not files in this folder)
# The customer-facing HTML pages themselves (index.html, category.html,
# product.html, catalogue.html, cart.html, about.html, contact.html) are
# served through the routes in app/web/site.py above, not this mount —
# that's what gives them clean URLs (/, /categories, /catalogue, ...)
# instead of a raw *.html path.

app.mount(
    "/assets",
    StaticFiles(directory=str(settings.frontend_root / "assets")),
    name="site-assets",
)

app.mount(
    "/admin/assets",
    StaticFiles(directory=str(settings.frontend_root / "admin" / "assets")),
    name="admin-assets",
)


# ======================================================
# Create Database Tables + Seed Default Admin
# ======================================================

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        auth_service.seed_default_admin(db)
    finally:
        db.close()


# ======================================================
# API Routes
# ======================================================

app.include_router(categories.router, prefix=settings.API_PREFIX)
app.include_router(sub_categories.router, prefix=settings.API_PREFIX)
app.include_router(products.router, prefix=settings.API_PREFIX)
app.include_router(catalogues.router, prefix=settings.API_PREFIX)
app.include_router(settings_router.router, prefix=settings.API_PREFIX)
app.include_router(upload.router, prefix=settings.API_PREFIX)


# ======================================================
# Health Check
# ======================================================

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "success": True,
        "message": "Badariya Flowers API is running",
        "version": settings.APP_VERSION,
    }


# ======================================================
# Redirect Exception Handler (require_login, etc.)
# ======================================================

@app.exception_handler(RedirectException)
async def redirect_exception_handler(request: Request, exc: RedirectException):
    return RedirectResponse(exc.url, status_code=status.HTTP_303_SEE_OTHER)


# ======================================================
# HTTP Error Handler
# ======================================================
# API and admin routes keep the original JSON error body. Anything else
# (a bad /category/{slug}, /product/{slug}, or just a typo'd URL on the
# public site) gets the site's own 404.html page instead of raw JSON.

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    path = request.url.path
    is_site_page = not (path.startswith("/api") or path.startswith("/admin"))
    if exc.status_code == status.HTTP_404_NOT_FOUND and is_site_page:
        return FileResponse(
            str(settings.frontend_root / "404.html"),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
        },
    )


# ======================================================
# Validation Error Handler
# ======================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation Error",
            "detail": exc.errors(),
        },
    )
