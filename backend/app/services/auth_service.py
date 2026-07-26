from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.admin_user import AdminUser


def get_admin_by_email(db: Session, email: str) -> Optional[AdminUser]:
    email = (email or "").strip().lower()
    return db.query(AdminUser).filter(AdminUser.email == email).first()


def get_admin_by_id(db: Session, admin_id: int) -> Optional[AdminUser]:
    return db.query(AdminUser).filter(AdminUser.id == admin_id).first()


def authenticate_admin(db: Session, email: str, password: str) -> Optional[AdminUser]:
    """Returns the AdminUser if the email/password pair is valid and the
    account is active, else None. Never raises for bad credentials — the
    caller decides how to present the failure."""
    admin = get_admin_by_email(db, email)
    if not admin or not admin.is_active:
        return None
    if not verify_password(password, admin.password_hash):
        return None
    return admin


def seed_default_admin(db: Session) -> None:
    """Creates the single bootstrap admin account the first time the app
    starts against an empty admin_users table. Safe to call on every
    startup — it's a no-op once any admin row exists, and never overwrites
    a password someone has since changed."""
    if db.query(AdminUser).first():
        return

    admin = AdminUser(
        name=settings.DEFAULT_ADMIN_NAME,
        email=settings.DEFAULT_ADMIN_EMAIL.strip().lower(),
        password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
        is_active=True,
    )
    db.add(admin)
    db.commit()
