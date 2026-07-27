"""
One-time-passwords issued during admin login (2FA step).

Flow:
    1. Admin submits email + password correctly.
    2. A 6-digit OTP is generated, HASHED (never stored in plain text),
       and emailed to the admin's own address.
    3. Admin submits the OTP on /admin/verify-otp.
    4. If it matches, isn't expired, and hasn't exceeded max attempts ->
       login completes and the row is marked used.

Only the hash is stored — same reasoning as passwords: if the database
ever leaks, no usable OTP leaks with it. A fresh row is created every
time an OTP is (re)sent; old unused rows for the same admin are simply
left to expire (harmless, since verify_otp always checks expiry).
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from app.database.base import Base


class AdminOtp(Base):
    __tablename__ = "admin_otps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Never store the raw OTP — same pbkdf2 hashing helpers used for
    # passwords (see app/core/security.py).
    otp_hash = Column(String(255), nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    is_used = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())