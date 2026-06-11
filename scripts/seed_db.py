"""
Creates the first admin user in the database.
Run this once before starting the app.

Usage:
    python scripts/seed_db.py
"""

import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from backend.app.db.session import SessionLocal, create_tables
from backend.app.services.auth_service import create_user, get_user_by_email
from backend.app.schemas.user import UserCreate
from backend.app.utils.logger import get_logger

logger = get_logger("seed_db")


def seed():
    create_tables()
    db = SessionLocal()

    admin_email = "admin@organization.com"
    admin_password = "Admin@1234"
    admin_name = "System Administrator"

    existing = get_user_by_email(db, admin_email)
    if existing:
        logger.info(f"Admin already exists: {admin_email}")
        db.close()
        return

    create_user(db, UserCreate(
        full_name=admin_name,
        email=admin_email,
        password=admin_password,
        role="admin",
    ))

    logger.info("=" * 50)
    logger.info("Admin account created successfully")
    logger.info(f"  Email    : {admin_email}")
    logger.info(f"  Password : {admin_password}")
    logger.info("  Change this password after first login!")
    logger.info("=" * 50)

    db.close()


if __name__ == "__main__":
    seed()