from sqlalchemy.orm import Session
from backend.app.models.user import User, UserRole
from backend.app.schemas.user import UserCreate
from backend.app.core.security import hash_password, verify_password
from backend.app.core.security import create_access_token
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def get_user_by_email(db: Session, email: str):
    """Fetches a user by email address."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Creates a new user account.
    Hashes the password before storing.
    """
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise ValueError(f"User with email {user_data.email} already exists.")

    hashed = hash_password(user_data.password)
    db_user = User(
        full_name=user_data.full_name,
        email=user_data.email.lower().strip(),
        hashed_password=hashed,
        role=UserRole(user_data.role),
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created: {db_user.email} | role={db_user.role}")
    return db_user


def authenticate_user(
    db: Session,
    email: str,
    password: str
) -> dict:
    """
    Authenticates a user with email and password.
    Returns a JWT token on success.
    Raises ValueError on failure.
    """
    user = get_user_by_email(db, email.lower().strip())

    if not user:
        raise ValueError("Invalid email or password.")

    if not user.is_active:
        raise ValueError(
            "Your account has been deactivated. "
            "Please contact the administrator."
        )

    if not verify_password(password, user.hashed_password):
        raise ValueError("Invalid email or password.")

    token = create_access_token(data={
        "sub": user.email,
        "role": user.role.value,
        "name": user.full_name,
    })

    logger.info(f"User authenticated: {user.email}")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_email": user.email,
        "user_role": user.role.value,
        "full_name": user.full_name,
    }

def get_all_users(db: Session, include_inactive: bool = False):
    """Returns all users, optionally including deactivated ones."""
    query = db.query(User)
    if not include_inactive:
        query = query.filter(User.is_active == True)
    return query.order_by(User.created_at.desc()).all()


def deactivate_user(db: Session, user_id: str) -> User:
    """Deactivates a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found.")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user