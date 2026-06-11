import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from pathlib import Path
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def extract_text_via_ocr(file_path: str) -> dict:
    """
    Fallback OCR parser for scanned PDF documents.
    Converts each page to an image and runs Tesseract OCR on it.
    Returns extracted text in the same structure as the PDF parser.
    """
    result = {
        "raw_text": "",
        "pages": [],
        "page_count": 0,
        "ocr_used": True,
    }

    try:
        logger.info(f"Running OCR on: {Path(file_path).name}")

        # Convert PDF pages to images at 300 DPI for good OCR accuracy
        pages = convert_from_path(file_path, dpi=300)
        result["page_count"] = len(pages)
        full_text_parts = []

        for page_num, page_image in enumerate(pages, start=1):
            # Run Tesseract on the image
            page_text = pytesseract.image_to_string(
                page_image,
                config="--oem 3 --psm 6",
            )

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

        logger.info(
            f"OCR complete: {Path(file_path).name} | "
            f"{result['page_count']} pages | "
            f"{len(result['raw_text'])} chars extracted"
        )

    except Exception as e:
        logger.error(f"OCR failed on {file_path}: {e}")
        raise

    return result