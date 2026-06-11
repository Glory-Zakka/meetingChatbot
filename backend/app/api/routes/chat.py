from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional
from backend.app.services.rag_service import ask_question
from backend.app.core.auth_guard import get_current_user
from backend.app.models.user import User
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
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    if len(request.question) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question too long. Keep it under 1000 characters.",
        )

    logger.info(
        f"Chat request | user={current_user.email} | "
        f"question={request.question[:60]}..."
    )

    try:
        result = ask_question(
            question=request.question,
            n_results=request.n_results,
            department_filter=request.department_filter,
            date_from=request.date_from,
            date_to=request.date_to,
        )
        return result

    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while processing your question.",
        )


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Chat service is running"}