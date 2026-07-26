"""
Small generic helper functions used across services.
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Query


# ==========================================================
# Pagination Helper
# ==========================================================

def paginate(
    query: Query,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Tuple[Query, int]:
    """
    Apply pagination to a SQLAlchemy query.

    Returns:
        (query, total_records)
    """

    total = query.count()

    if page is None or page_size is None:
        return query, total

    page = max(page, 1)

    offset = (page - 1) * page_size

    query = query.offset(offset).limit(page_size)

    return query, total


# ==========================================================
# Boolean Parser
# ==========================================================

def parse_bool(value: Optional[str]) -> Optional[bool]:
    """
    Convert common string values to boolean.

    Examples:

    true
    false
    yes
    no
    1
    0
    on
    off
    """

    if value is None:
        return None

    value = value.strip().lower()

    if value in ("true", "1", "yes", "on"):
        return True

    if value in ("false", "0", "no", "off"):
        return False

    return None