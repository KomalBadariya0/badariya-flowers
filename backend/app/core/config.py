"""
Application configuration.

All values are read from environment variables (see .env.example at the
project root). Nothing here should be hardcoded for production — copy
.env.example to .env and fill in real values before running the app.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # ---- App ----
    APP_NAME: str = "Badariya Flowers API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # ---- MySQL ----
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "badariya_flowers"
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""

    # ---- Uploads ----
    UPLOAD_PATH: str = "uploads"
    MAX_IMAGE_SIZE_MB: int = 5
    MAX_PDF_SIZE_MB: int = 20

    # ---- Frontend (sibling project folder) ----
    # The existing frontend/ project (unchanged) lives next to backend/.
    # We serve its assets directly — /assets -> frontend/assets,
    # /admin -> frontend/admin — so pages that haven't been migrated to
    # Jinja2 yet keep working exactly as before, and the new server-
    # rendered admin pages can reuse the exact same CSS/images with zero
    # duplication. Override with FRONTEND_DIR in .env if the folder lives
    # somewhere else on a given machine.
    #
    # Project layout:
    #   project-root/
    #     backend/        <- this app
    #     admin/           <- admin panel (static pages + Jinja2-rendered
    #                        Categories page mounted at /admin/categories)
    #     assets/          <- shared site design tokens, images, fonts
    #     index.html, category.html, ...  <- customer-facing site (untouched)
    # So frontend_root == project-root == one level up from backend/.
    FRONTEND_DIR: str = ".."

    # ---- CORS ----
    # Comma separated list of allowed origins, e.g.
    # "http://localhost:5500,http://127.0.0.1:5500,https://badariyaflowers.com"
    CORS_ORIGINS: str = "*"

    # ---- Admin Session / Auth ----
    # Signs the admin login session cookie (Starlette SessionMiddleware).
    # Override with a long random value in .env for production.
    SESSION_SECRET_KEY: str = "badariya-flowers-dev-secret-change-me-in-production"
    SESSION_COOKIE_NAME: str = "bf_admin_session"
    # Session cookie lifetime in seconds (default: 7 days) — "remember login"
    # across browser refreshes/restarts until logout.
    SESSION_MAX_AGE: int = 7 * 24 * 60 * 60

    # ---- Initial Admin Seed ----
    # A single admin row is created automatically on first startup if the
    # admin_users table is empty. Change the password from the admin
    # panel (or here before first run) — this is only a bootstrap value.
    DEFAULT_ADMIN_EMAIL: str = "admin@badariyaflowers.com"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    DEFAULT_ADMIN_NAME: str = "Badariya Admin"

    # ---- Admin Login OTP (2FA) ----
    # After email+password checks out, a 6-digit OTP is emailed to the
    # admin's own email address. Login only completes once that OTP is
    # verified. Override all of this via .env for production.
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    # "From" address shown on the OTP email. Falls back to SMTP_USERNAME
    # if left blank.
    MAIL_FROM_EMAIL: str = ""
    MAIL_FROM_NAME: str = "Badariya Flowers Admin"

    OTP_LENGTH: int = 6
    OTP_EXPIRY_SECONDS: int = 5 * 60  # OTP valid for 5 minutes
    OTP_MAX_ATTEMPTS: int = 5         # wrong tries allowed before OTP is voided
    OTP_RESEND_COOLDOWN_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """SQLAlchemy connection string (PyMySQL driver)."""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        )

    @property
    def upload_root(self) -> Path:
        path = BACKEND_ROOT / self.UPLOAD_PATH
        path.mkdir(parents=True, exist_ok=True)
        for sub in ("products", "categories", "catalogues", "logos"):
            (path / sub).mkdir(parents=True, exist_ok=True)
        return path

    @property
    def frontend_root(self) -> Path:
        """Absolute path to the sibling frontend/ project folder."""
        path = (BACKEND_ROOT / self.FRONTEND_DIR).resolve()
        return path

    @property
    def templates_dir(self) -> Path:
        return BACKEND_ROOT / "app" / "templates"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()