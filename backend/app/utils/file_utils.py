import os
from pathlib import Path
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def is_allowed_file(filename: str) -> bool:
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def detect_file_type(file_path: str) -> str:
    """Returns 'pdf' or 'docx' based on file extension."""
    ext = get_file_extension(file_path)
    if ext == ".pdf":
        return "pdf"
    elif ext == ".docx":
        return "docx"
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def get_file_size(file_path: str) -> int:
    """Returns file size in bytes."""
    return os.path.getsize(file_path)


def ensure_directory(path: str) -> None:
    """Creates directory if it does not exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def safe_filename(filename: str) -> str:
    """Strips unsafe characters from a filename."""
    name = Path(filename).stem
    ext = Path(filename).suffix
    safe = "".join(
        c if c.isalnum() or c in ("-", "_") else "_" for c in name
    )
    return f"{safe}{ext}"