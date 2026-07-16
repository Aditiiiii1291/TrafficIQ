"""Database session helper for TrafficIQ."""

from sqlalchemy.orm import sessionmaker
from backend.database.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency provider yielding database sessions, closing them afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
