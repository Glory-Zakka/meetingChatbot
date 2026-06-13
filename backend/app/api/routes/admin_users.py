from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.auth_guard import require_admin
from backend.app.db.session import get_db
from backend.app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
async def list_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin-only endpoint to list all users."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {
        "total": len(users),
        "users": [
            {
                "id": str(u.id),
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }