from collections.abc import Generator

from sqlalchemy import (
    create_engine,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)

from work_order_api.config import settings

class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

def get_db() -> Generator[Session, None, None]:
    """Provide a database session for a request."""

    database = SessionLocal()

    try:
        yield database

    finally:
        database.close()

def check_database_connection() -> None:
    """Verify that PostgreSQL can be reached."""

    with engine.connect() as connection:
        connection.execute(
            text("SELECT 1")
        )
