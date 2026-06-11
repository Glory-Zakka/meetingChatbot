from fastapi import HTTPException, status
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def verify_internal_request():
    """
    Placeholder dependency for request verification.
    Will be replaced with full JWT auth in Phase 4.
    """
    return True