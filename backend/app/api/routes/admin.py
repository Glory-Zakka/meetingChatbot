import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from backend.app.core.auth_guard import get_current_user, require_admin
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.services.audit_service import log_action, get_audit_logs
from backend.app.utils.file_utils import (
    is_allowed_file,
    get_file_size,
    ensure_directory,
    safe_filename,
)
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

UPLOAD_DIR = (
    "/teamspace/studios/this_studio/meeting_minutes/storage/documents"
)
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin-only endpoint to upload a new meeting document.
    Requires role=admin at the server side.
    """
    if not is_allowed_file(file.filename):
        log_action(
            db, current_user, "upload",
            "document", file.filename,
            status="failed",
            details={"reason": "invalid file type"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum 50MB allowed.",
        )

    ensure_directory(UPLOAD_DIR)
    safe_name = safe_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    # Idempotency check — don't re-process the same file
    if os.path.exists(file_path):
        existing_chunks = _count_chunks_for_file(safe_name)
        if existing_chunks > 0:
            log_action(
                db, current_user, "upload",
                "document", safe_name,
                status="failed",
                details={"reason": "duplicate file"},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Document '{safe_name}' has already been "
                    f"uploaded and processed."
                ),
            )

    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        log_action(
            db, current_user, "upload",
            "document", safe_name,
            status="failed",
            details={"reason": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )

    file_size = get_file_size(file_path)
    logger.info(
        f"File uploaded by {current_user.email}: "
        f"{safe_name} ({file_size} bytes)"
    )

    from backend.app.services.ingestion_service import ingest_document

    result = ingest_document(
        file_path=file_path,
        original_filename=safe_name,
        db=db,
        uploaded_by=current_user.email,
    )

    if not result["success"]:
        try:
            os.remove(file_path)
        except OSError:
            pass
        log_action(
            db, current_user, "upload",
            "document", safe_name,
            status="failed",
            details={"reason": result.get("error")},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {result.get('error')}",
        )

    log_action(
        db, current_user, "upload",
        "document", safe_name,
        details={
            "file_size": file_size,
            "chunks": result["total_chunks"],
            "metadata": result["metadata"],
        },
    )

    return {
        "success": True,
        "file_name": safe_name,
        "file_size_bytes": file_size,
        "total_chunks": result["total_chunks"],
        "metadata": result["metadata"],
    }


@router.delete("/documents/{file_name}")
async def delete_document(
    file_name: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin-only endpoint to delete a meeting document.
    Removes the file from storage AND all chunks from ChromaDB.
    """
    file_path = os.path.join(UPLOAD_DIR, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{file_name}' not found.",
        )

    # Get chunk count before deletion for the log
    chunks_deleted = _count_chunks_for_file(file_name)

    # Remove the file from storage
    try:
        os.remove(file_path)
    except Exception as e:
        logger.error(f"Failed to remove file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}",
        )

    # Remove all chunks from ChromaDB
    try:
        from backend.app.pipeline.vector_store.chroma_store import (
            get_or_create_collection,
        )
        collection = get_or_create_collection()
        collection.delete(where={"document_name": file_name})
    except Exception as e:
        logger.error(f"Failed to remove chunks for {file_name}: {e}")

    log_action(
        db, current_user, "delete",
        "document", file_name,
        details={"chunks_deleted": chunks_deleted},
    )

    logger.info(
        f"Document deleted by {current_user.email}: "
        f"{file_name} ({chunks_deleted} chunks)"
    )

    return {
        "success": True,
        "file_name": file_name,
        "chunks_deleted": chunks_deleted,
    }


@router.get("/documents")
async def list_documents(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only endpoint to list all uploaded documents."""
    ensure_directory(UPLOAD_DIR)
    documents = []
    folder = Path(UPLOAD_DIR)

    for file_path in folder.glob("*"):
        if file_path.suffix.lower() in [".pdf", ".docx"]:
            documents.append({
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "file_type": file_path.suffix.lstrip(".").lower(),
                "modified": file_path.stat().st_mtime,
                "chunks": _count_chunks_for_file(file_path.name),
            })

    documents.sort(key=lambda x: x["modified"], reverse=True)

    return {"total": len(documents), "documents": documents}


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only endpoint to view system statistics."""
    from backend.app.pipeline.vector_store.chroma_store import (
        get_collection_stats,
    )

    ensure_directory(UPLOAD_DIR)
    doc_count = len([
        f for f in Path(UPLOAD_DIR).glob("*")
        if f.suffix.lower() in [".pdf", ".docx"]
    ])

    user_count = db.query(User).count()
    active_user_count = (
        db.query(User).filter(User.is_active == True).count()
    )

    chroma_stats = get_collection_stats()

    return {
        "total_documents": doc_count,
        "total_chunks": chroma_stats["total_chunks"],
        "total_users": user_count,
        "active_users": active_user_count,
    }


@router.get("/audit-logs")
async def get_audit_logs_endpoint(
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    user_email: str = Query(default=None),
    action: str = Query(default=None),
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin-only endpoint to view the system audit log.
    Supports filtering by user, action type, and date range.
    """
    logs, total = get_audit_logs(
        db,
        limit=limit,
        offset=offset,
        user_email=user_email,
        action=action,
        date_from=date_from,
        date_to=date_to,
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": [
            {
                "id": str(log.id),
                "user_email": log.user_email,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "status": log.status,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }


# ── Helper functions ───────────────────────────────────────
def _count_chunks_for_file(file_name: str) -> int:
    """Counts chunks in ChromaDB belonging to a specific document."""
    try:
        from backend.app.pipeline.vector_store.chroma_store import (
            get_or_create_collection,
        )
        collection = get_or_create_collection()
        result = collection.get(where={"document_name": file_name})
        return len(result.get("ids", []))
    except Exception:
        return 0