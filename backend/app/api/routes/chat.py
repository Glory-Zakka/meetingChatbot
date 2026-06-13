from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel
from typing import Optional
from backend.app.services.rag_service import ask_question
from backend.app.core.auth_guard import get_current_user
from backend.app.models.user import User
from backend.app.db.session import get_db
from backend.app.services.audit_service import log_action
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str
    department_filter: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    n_results: Optional[int] = 5


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list
    chunks_retrieved: int


@router.post("/ask", response_model=ChatResponse)
async def ask(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Main chat endpoint. Requires valid JWT token.
    Logs every query for audit purposes.
    """
    if not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    if len(payload.question) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question too long. Keep it under 1000 characters.",
        )

    client_ip = request.client.host if request.client else None
    logger.info(
        f"Chat request | user={current_user.email} | "
        f"question={payload.question[:60]}..."
    )

    try:
        result = ask_question(
            question=payload.question,
            n_results=payload.n_results,
            department_filter=payload.department_filter,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )

        # Log the query
        log_action(
            db, current_user, "chat_query",
            details={
                "question": payload.question,
                "chunks_retrieved": result.get("chunks_retrieved", 0),
                "sources_count": len(result.get("sources", [])),
            },
            ip_address=client_ip,
        )

        return result

    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        log_action(
            db, current_user, "chat_query",
            status="failed",
            details={"question": payload.question, "error": str(e)},
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while processing your question.",
        )


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Chat service is running"}