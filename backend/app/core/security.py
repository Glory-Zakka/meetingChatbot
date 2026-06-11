from datetime import datetime, timedelta
from typing import Optional
import hashlib
import hmac
from jose import JWTError, jwt
from backend.app.config import settings
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with a static app secret.
    This is simpler and avoids bcrypt backend issues in this environment.
    """
    secret = settings.jwt_secret_key.encode("utf-8")
    return hmac.new(secret, password.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its stored hash."""
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        return None