import uuid
from sqlalchemy.orm import Session

from backend.app.pipeline.parser.pdf_parser import extract_text_from_pdf
from backend.app.pipeline.parser.docx_parser import extract_text_from_docx
from backend.app.pipeline.parser.ocr_parser import extract_text_via_ocr
from backend.app.pipeline.parser.metadata_extractor import extract_metadata
from backend.app.pipeline.chunker.text_chunker import (
    chunk_text,
    chunk_by_section,
)
from backend.app.pipeline.embedder.openai_embedder import embed_texts
from backend.app.pipeline.vector_store.chroma_store import store_chunks
from backend.app.utils.file_utils import detect_file_type
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def ingest_document(
    file_path: str,
    original_filename: str,
    db: Session = None,
    uploaded_by: str = "system",
    document_id: str = None,
) -> dict:
    """
    Master ingestion function. Orchestrates the full pipeline:
    parse → extract metadata → chunk → embed → store in ChromaDB.

    db is optional so this function can be called from the
    batch script without a live database session.

    Returns a summary dict of the ingestion result.
    """
    doc_id = document_id or str(uuid.uuid4())
    file_type = detect_file_type(file_path)

    logger.info(
        f"Starting ingestion | file={original_filename} | "
        f"type={file_type} | id={doc_id}"
    )

    try:
        # ── STEP 1: Parse the document ──────────────────────────────
        logger.info("Step 1: Parsing document...")

        if file_type == "pdf":
            parsed = extract_text_from_pdf(file_path)
            raw_text = parsed["raw_text"]
            sections = None

            # Fallback to OCR if insufficient text found
            if parsed.get("needs_ocr"):
                logger.info("Insufficient text found. Falling back to OCR...")
                ocr_result = extract_text_via_ocr(file_path)
                raw_text = ocr_result["raw_text"]

        elif file_type == "docx":
            parsed = extract_text_from_docx(file_path)
            raw_text = parsed["raw_text"]
            sections = parsed.get("sections")

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        if not raw_text.strip():
            raise ValueError(
                "No text could be extracted from the document."
            )

        logger.info(f"Parsed {len(raw_text)} characters")

        # ── STEP 2: Extract metadata ────────────────────────────────
        logger.info("Step 2: Extracting metadata...")
        metadata = extract_metadata(raw_text, filename=original_filename)

        # ── STEP 3: Chunk the text ──────────────────────────────────
        logger.info("Step 3: Chunking text...")
        if file_type == "docx" and sections:
            chunks = chunk_by_section(sections)
        else:
            chunks = chunk_text(raw_text)

        if not chunks:
            raise ValueError("No chunks produced from the document.")

        logger.info(f"Produced {len(chunks)} chunks")

        # ── STEP 4: Generate embeddings ─────────────────────────────
        logger.info("Step 4: Generating embeddings...")
        embeddings = embed_texts(chunks)

        # ── STEP 5: Store in ChromaDB ───────────────────────────────
        logger.info("Step 5: Storing in ChromaDB...")
        chunk_ids = store_chunks(
            chunks=chunks,
            embeddings=embeddings,
            document_id=doc_id,
            document_name=original_filename,
            metadata=metadata,
        )

        logger.info(
            f"Ingestion complete | file={original_filename} | "
            f"chunks={len(chunks)}"
        )

        return {
            "success": True,
            "document_id": doc_id,
            "file_name": original_filename,
            "total_chunks": len(chunks),
            "metadata": {
                "meeting_date": (
                    metadata["meeting_date"].isoformat()
                    if metadata.get("meeting_date") else None
                ),
                "department": metadata.get("department"),
                "attendees": metadata.get("attendees"),
                "agenda_items": metadata.get("agenda_items"),
                "decisions_made": metadata.get("decisions_made"),
                "action_items": metadata.get("action_items"),
            },
        }

    except Exception as e:
        logger.error(f"Ingestion failed for {original_filename}: {e}")
        return {
            "success": False,
            "document_id": doc_id,
            "file_name": original_filename,
            "error": str(e),
        }