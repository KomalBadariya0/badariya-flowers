"""
Admin > Dashboard — server-rendered overview page.

Route map:
    GET  /admin/dashboard   full page: live counts + 5 most recent products
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.models.category import Category
from app.models.catalogue import Catalogue
from app.models.product import Product
from app.models.sub_category import SubCategory
from app.web.deps import require_login, templates

router = APIRouter(prefix="/admin/dashboard", tags=["Admin · Dashboard"], dependencies=[Depends(require_login)])


@router.get("")
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    stats = {
        "categories": db.query(Category).count(),
        "subcategories": db.query(SubCategory).count(),
        "products": db.query(Product).count(),
        "catalogues": db.query(Catalogue).count(),
    }

    recent_products = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.images))
        .order_by(Product.created_at.desc())
        .limit(5)
        .all()
    )

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "active_page": "dashboard",
            "stats": stats,
            "recent_products": recent_products,
        },
    )
