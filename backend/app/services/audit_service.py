from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def log_action(
    db: Session,
    user: Optional[User],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    status: str = "success",
) -> AuditLog:
    """
    Records a significant system action to the audit log.
    Used for login attempts, queries, uploads, deletions, and user changes.
    """
    try:
        log_entry = AuditLog(
            user_id=user.id if user else None,
            user_email=user.email if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            status=status,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
        db.rollback()
        return None


def get_audit_logs(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    user_email: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """
    Retrieves audit log entries with optional filtering.
    Returns a list of log entries and the total count.
    """
    query = db.query(AuditLog)

    if user_email:
        query = query.filter(AuditLog.user_email == user_email)
    if action:
        query = query.filter(AuditLog.action == action)
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)

    total = query.count()
    logs = (
        query.order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return logs, total