"""
SQLAlchemy engine/session setup. One engine per process, one session per request.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    """FastAPI dependency: yields a DB session and guarantees it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
