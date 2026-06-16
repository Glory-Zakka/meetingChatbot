import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator


# Check for USE_SQLITE environment variable
use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"

if use_sqlite:
    DATABASE_URL = "sqlite:///./meeting_chatbot.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    print("Using SQLite database")
else:
    # Build from environment variables directly
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "meeting_chatbot")
    pg_user = os.getenv("POSTGRES_USER", "postgres")
    pg_pass = os.getenv("POSTGRES_PASSWORD", "postgres")
    DATABASE_URL = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    print(f"Using PostgreSQL database at {pg_host}:{pg_port}")


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from backend.app.db.base import Base
    import backend.app.models.user
    import backend.app.models.audit_log
    Base.metadata.create_all(bind=engine)