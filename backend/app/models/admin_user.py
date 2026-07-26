from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.database.base import Base


class AdminUser(Base):
    """A single admin account (or a handful, if created manually later).

    There is intentionally no public signup endpoint — rows in this table
    are only ever created by the startup seed (see
    app/services/auth_service.py::seed_default_admin) or added directly to
    the database by whoever manages the deployment.
    """

    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False, default="Admin")
    email = Column(String(190), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
