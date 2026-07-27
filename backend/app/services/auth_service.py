import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.admin_otp import AdminOtp
from app.models.admin_user import AdminUser
from app.utils.mailer import send_email_change_otp_email, send_otp_email


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


def _generate_otp_code() -> str:
    """Cryptographically random N-digit code (N = settings.OTP_LENGTH),
    zero-padded (e.g. "042817"), generated with secrets — not random —
    since this gates access to the admin panel."""
    upper_bound = 10 ** settings.OTP_LENGTH
    return str(secrets.randbelow(upper_bound)).zfill(settings.OTP_LENGTH)


def get_latest_otp(db: Session, admin_id: int) -> Optional[AdminOtp]:
    return (
        db.query(AdminOtp)
        .filter(AdminOtp.admin_id == admin_id)
        .order_by(AdminOtp.id.desc())
        .first()
    )


def seconds_until_resend_allowed(db: Session, admin_id: int) -> int:
    """0 if the admin can request a new OTP right now, else how many
    seconds they still have to wait (used to disable the Resend button
    and stop someone from spamming their own inbox)."""
    latest = get_latest_otp(db, admin_id)
    if not latest or not latest.created_at:
        return 0
    created_at = latest.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    elapsed = (datetime.now(timezone.utc) - created_at).total_seconds()
    remaining = settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed
    return max(0, int(remaining))


def create_and_send_otp(db: Session, admin: AdminUser) -> AdminOtp:
    """Generates a fresh OTP, stores only its hash, emails the plain code
    to the admin's own address, and returns the new AdminOtp row.

    Raises whatever send_otp_email raises (e.g. an smtplib error) if the
    email can't be sent — the row is still committed either way so a
    subsequent "Resend" attempt doesn't need special-casing, but callers
    should treat a raised exception here as "OTP not delivered" and tell
    the admin to try resending rather than silently continuing."""
    code = _generate_otp_code()
    otp = AdminOtp(
        admin_id=admin.id,
        otp_hash=hash_password(code),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.OTP_EXPIRY_SECONDS),
        attempts=0,
        is_used=False,
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)

    send_otp_email(admin.email, code, expiry_minutes=settings.OTP_EXPIRY_SECONDS // 60)
    return otp


def create_and_send_email_change_otp(db: Session, admin: AdminUser, new_email: str) -> AdminOtp:
    """Same pattern as create_and_send_otp, but for confirming an admin's
    NEW email address before the account's login email is switched to it.

    The code is mailed to `new_email` (not admin.email) — this is the
    whole point: it proves the admin actually controls that inbox before
    it becomes their login email. The OTP row itself is still keyed by
    admin_id, so verify_otp / seconds_until_resend_allowed work exactly
    as they already do for login — no changes needed there.
    """
    code = _generate_otp_code()
    otp = AdminOtp(
        admin_id=admin.id,
        otp_hash=hash_password(code),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.OTP_EXPIRY_SECONDS),
        attempts=0,
        is_used=False,
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)

    send_email_change_otp_email(new_email, code, expiry_minutes=settings.OTP_EXPIRY_SECONDS // 60)
    return otp


def verify_otp(db: Session, admin_id: int, code: str) -> tuple[bool, Optional[str]]:
    """Checks `code` against the most recent (unused) OTP for this admin.

    Returns (True, None) on success, or (False, "reason") on failure —
    the reason is a user-facing message (expired / too many attempts /
    incorrect / none requested), never an internal detail.
    """
    otp = get_latest_otp(db, admin_id)
    if not otp or otp.is_used:
        return False, "No active code found. Please request a new one."

    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        return False, "Too many incorrect attempts. Please request a new code."

    expires_at = otp.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        return False, "This code has expired. Please request a new one."

    if not verify_password((code or "").strip(), otp.otp_hash):
        otp.attempts += 1
        db.commit()
        remaining = settings.OTP_MAX_ATTEMPTS - otp.attempts
        if remaining <= 0:
            return False, "Too many incorrect attempts. Please request a new code."
        return False, f"Incorrect code. {remaining} attempt(s) remaining."

    otp.is_used = True
    db.commit()
    return True, None


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