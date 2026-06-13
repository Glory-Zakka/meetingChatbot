from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.schemas.auth import LoginRequest, TokenResponse
from backend.app.schemas.user import UserCreate, UserResponse
from backend.app.services.auth_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    deactivate_user,
)
from backend.app.core.auth_guard import get_current_user, require_admin
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.services.audit_service import log_action
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """Staff login endpoint. Logs both successful and failed attempts."""
    client_ip = request.client.host if request.client else None
    try:
        result = authenticate_user(
            db=db,
            email=payload.email,
            password=payload.password,
        )
        # Log successful login
        user = get_user_by_email(db, payload.email.lower().strip())
        log_action(
            db, user, "login",
            status="success",
            ip_address=client_ip,
        )
        return result
    except ValueError as e:
        # Log failed login attempt
        log_action(
            db, None, "login",
            status="failed",
            details={"email": payload.email, "reason": str(e)},
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin-only endpoint to create a new user account."""
    try:
        user = create_user(db=db, user_data=user_data)
        log_action(
            db, admin, "create_user",
            "user", user.email,
            details={"role": user.role.value},
        )
        return UserResponse(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Returns the current authenticated user's profile."""
    return UserResponse(
        id=str(current_user.id),
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user_endpoint(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin-only endpoint to deactivate a user account.
    Deactivated users cannot log in.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account.",
        )

    user.is_active = False
    db.commit()

    log_action(
        db, admin, "deactivate_user",
        "user", user.email,
    )

    return {"success": True, "email": user.email, "is_active": False}


@router.patch("/users/{user_id}/activate")
async def activate_user_endpoint(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin-only endpoint to reactivate a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user.is_active = True
    db.commit()

    log_action(
        db, admin, "activate_user",
        "user", user.email,
    )

    return {"success": True, "email": user.email, "is_active": True}