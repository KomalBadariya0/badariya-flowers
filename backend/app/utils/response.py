"""
Generic API Response Helpers

Provides a consistent response format across the application.
"""

from typing import Any, Optional


# ==========================================================
# Success Response
# ==========================================================

def success_response(
    data: Any = None,
    message: str = "Success",
) -> dict:
    """
    Standard success response.

    Example:
    {
        "success": True,
        "message": "Category Created",
        "data": {...}
    }
    """

    return {
        "success": True,
        "message": message,
        "data": data,
    }


# ==========================================================
# Error Response
# ==========================================================

def error_response(
    message: str,
    detail: Optional[Any] = None,
) -> dict:
    """
    Standard error response.

    Example:
    {
        "success": False,
        "message": "Category Not Found",
        "detail": {...}
    }
    """

    return {
        "success": False,
        "message": message,
        "detail": detail,
    }