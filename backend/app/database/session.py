"""
Engine, session factory and the get_db() FastAPI dependency.

Usage in a router:

    from app.database.session import get_db

    @router.get("/")
    def list_things(db: Session = Depends(get_db)):
        ...
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# pool_pre_ping avoids "MySQL server has gone away" errors on idle
# connections; pool_recycle keeps connections fresh well under MySQL's
# default wait_timeout.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG and settings.ENVIRONMENT == "development",
    future=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()