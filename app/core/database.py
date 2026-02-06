"""Database setup for Mirrarr using SQLModel."""

from sqlmodel import SQLModel, Session, create_engine
from app.core.config import get_settings

settings = get_settings()

# Create engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},  # Needed for SQLite
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency that provides a database session."""
    with Session(engine) as session:
        yield session
