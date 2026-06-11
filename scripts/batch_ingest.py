"""
Batch ingestion script — run this to load all existing
meeting documents into the system at once.

Usage:
    python scripts/batch_ingest.py --folder /path/to/your/meeting/docs
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path so backend imports work
sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from backend.app.services.ingestion_service import ingest_document
from backend.app.utils.logger import get_logger

logger = get_logger("batch_ingest")


def run_batch_ingest(folder: str, extensions: list):
    folder_path = Path(folder)

    if not folder_path.exists():
        logger.error(f"Folder not found: {folder}")
        sys.exit(1)

    # Collect all matching files
    files = []
    for ext in extensions:
        files.extend(folder_path.glob(f"**/*.{ext}"))

    if not files:
        logger.warning(
            f"No files with extensions {extensions} "
            f"found in {folder}"
        )
        return

    logger.info(
        f"Found {len(files)} documents to ingest from {folder}"
    )

    results = {"success": 0, "failed": 0}

    for file_path in files:
        file_path_str = str(file_path)
        original_name = file_path.name

        logger.info(f"Processing: {original_name}")

        result = ingest_document(
            file_path=file_path_str,
            original_filename=original_name,
            uploaded_by="batch_script",
        )

        if result["success"]:
            results["success"] += 1
            logger.info(
                f"Done: {original_name} | "
                f"{result['total_chunks']} chunks | "
                f"date={result['metadata'].get('meeting_date')} | "
                f"dept={result['metadata'].get('department')}"
            )
        else:
            results["failed"] += 1
            logger.error(
                f"Failed: {original_name} | {result.get('error')}"
            )

    # Final summary
    logger.info("=" * 50)
    logger.info("Batch ingestion complete")
    logger.info(f"  Success : {results['success']}")
    logger.info(f"  Failed  : {results['failed']}")
    logger.info("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch ingest meeting documents."
    )
    parser.add_argument(
        "--folder",
        type=str,
        required=True,
        help="Path to the folder containing meeting documents",
    )
    parser.add_argument(
        "--ext",
        nargs="+",
        default=["pdf", "docx"],
        help="File extensions to process (default: pdf docx)",
    )
    args = parser.parse_args()
    run_batch_ingest(args.folder, args.ext)