"""Database connection and session management."""

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import OperationalError

from app.config import DATABASE_URL
from app.database.models import Base

logger = logging.getLogger(__name__)

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _add_password_hash_column_if_missing():
    """Add users.password_hash column for existing DBs created before auth was added."""
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
        logger.info("Added users.password_hash column")
    except OperationalError as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            pass  # Column already there
        else:
            raise


def init_db():
    """Initialize database tables and run any needed migrations."""
    Base.metadata.create_all(bind=engine)
    if DATABASE_URL.startswith("sqlite"):
        _add_password_hash_column_if_missing()


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
