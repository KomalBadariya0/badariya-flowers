"""
Project Constants

Common constant values shared across the application.
"""

# ==========================================================
# Status
# ==========================================================

STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"

STATUS_CHOICES = (
    STATUS_ACTIVE,
    STATUS_INACTIVE,
)


# ==========================================================
# Catalogue Types
# ==========================================================

CATALOGUE_TYPE_MASTER = "master"
CATALOGUE_TYPE_CATEGORY = "category"

CATALOGUE_TYPE_CHOICES = (
    CATALOGUE_TYPE_MASTER,
    CATALOGUE_TYPE_CATEGORY,
)


# ==========================================================
# Upload Folder Names
# ==========================================================

UPLOAD_PRODUCTS = "products"
UPLOAD_CATEGORIES = "categories"
UPLOAD_CATALOGUES = "catalogues"
UPLOAD_LOGOS = "logos"

UPLOAD_SUBDIRS = (
    UPLOAD_PRODUCTS,
    UPLOAD_CATEGORIES,
    UPLOAD_CATALOGUES,
    UPLOAD_LOGOS,
)


# ==========================================================
# Default Settings
# ==========================================================

DEFAULT_PRODUCTS_PER_PAGE = 12