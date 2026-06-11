import fitz  # PyMuPDF
from pathlib import Path
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extracts full text from a PDF file page by page.
    Returns a dict with raw text and per-page content.
    Flags document for OCR if no text is found.
    """
    result = {
        "raw_text": "",
        "pages": [],
        "page_count": 0,
        "needs_ocr": False,
    }

    try:
        doc = fitz.open(file_path)
        result["page_count"] = len(doc)
        full_text_parts = []

        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text")

            # Clean up excessive whitespace
            cleaned = "\n".join(
                line.strip()
                for line in page_text.splitlines()
                if line.strip()
            )

            result["pages"].append({
                "page_number": page_num,
                "text": cleaned,
            })

            if cleaned:
                full_text_parts.append(cleaned)

        result["raw_text"] = "\n\n".join(full_text_parts)

        # Flag for OCR if very little text was extracted
        if len(result["raw_text"].strip()) < 50:
            logger.warning(
                f"Very little text extracted from {file_path}. "
                f"Flagging for OCR."
            )
            result["needs_ocr"] = True

        doc.close()
        logger.info(
            f"PDF parsed: {Path(file_path).name} | "
            f"{result['page_count']} pages | "
            f"{len(result['raw_text'])} chars"
        )

    except Exception as e:
        logger.error(f"Failed to parse PDF {file_path}: {e}")
        raise

    return result