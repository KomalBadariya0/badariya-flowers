"""
Backward-compatible database exports.

This module simply re-exports the shared SQLAlchemy objects.
"""

from app.database.base import Base
from app.database.session import (
    engine,
    SessionLocal,
    get_db,
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
]