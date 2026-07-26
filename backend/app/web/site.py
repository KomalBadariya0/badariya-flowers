"""
Public customer-facing website routes.

Everything here runs on the exact same FastAPI app / port as the admin
panel and the JSON API — no separate static file server, no other ports.

The actual pages are the existing static HTML files at the project root
(index.html, category.html, product.html, catalogue.html, cart.html) —
they're entirely client-rendered (fetch the JSON API, build the DOM with
plain JS). These routes just serve the right file at a clean URL:

    GET /                -> index.html
    GET /about           -> about.html
    GET /categories       -> category.html   (all-categories / ?cat= / ?sub=)
    GET /category/{slug} -> looks the category up by slug, then redirects
                             to /categories?cat={slug} (the page that
                             actually renders it — same content, and a
                             single path segment keeps every relative
                             asset reference on the page working)
    GET /product/{slug}  -> looks the product up by its SEO slug, then
                             redirects to /product.html?sub=..&no=.. (the
                             sub-category slug + display number the page's
                             existing client-side lookup already expects)
    GET /contact         -> contact.html
    GET /catalogue        -> catalogue.html
    GET /cart             -> cart.html

404s for anything else (assets aside) fall through to the app-wide
StarletteHTTPException handler in main.py, which serves 404.html for
non-API/non-admin paths.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.database.session import get_db
from app.models.category import Category
from app.models.product import Product

router = APIRouter(tags=["Website"])


def _page(filename: str) -> FileResponse:
    return FileResponse(str(settings.frontend_root / filename))


@router.get("/")
def home_page():
    return _page("index.html")


@router.get("/about")
def about_page():
    return _page("about.html")


@router.get("/contact")
def contact_page():
    return _page("contact.html")


@router.get("/catalogue")
def catalogue_page():
    return _page("catalogue.html")


@router.get("/cart")
def cart_page():
    return _page("cart.html")


@router.get("/categories")
def categories_page():
    return _page("category.html")


@router.get("/category/{slug}")
def category_by_slug(slug: str, db: Session = Depends(get_db)):
    exists = db.query(Category.id).filter(Category.slug == slug).first()
    if not exists:
        raise StarletteHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return RedirectResponse(f"/categories?cat={slug}", status_code=status.HTTP_302_FOUND)


@router.get("/product.html")
def product_page_alias():
    """Alias so the absolute `/product.html?sub=..&no=..` links used
    throughout the site (product cards, search results, breadcrumbs)
    resolve — the real content is the same product.html file /product/{slug}
    redirects into below."""
    return _page("product.html")


@router.get("/product/{slug}")
def product_by_slug(slug: str, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .options(joinedload(Product.sub_category))
        .filter(Product.seo_slug == slug)
        .first()
    )
    if not product or not product.sub_category:
        raise StarletteHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return RedirectResponse(
        f"/product.html?sub={product.sub_category.slug}&no={product.no}",
        status_code=status.HTTP_302_FOUND,
    )
