"""
Quick end-to-end test of the ingestion pipeline.
Run after batch_ingest.py to verify retrieval is working.

Usage:
    python scripts/test_pipeline.py --query "What was decided in the last meeting?"
"""

import sys
import argparse
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from backend.app.pipeline.embedder.openai_embedder import embed_query
from backend.app.pipeline.vector_store.chroma_store import (
    query_collection,
    get_collection_stats,
)
from backend.app.utils.logger import get_logger

logger = get_logger("test_pipeline")


def run_test(query: str, n_results: int = 5):
    logger.info("=" * 50)
    logger.info("Pipeline Test")
    logger.info("=" * 50)

    # Check collection stats
    stats = get_collection_stats()
    logger.info(f"ChromaDB stats: {stats}")

    if stats["total_chunks"] == 0:
        logger.error(
            "No chunks found in ChromaDB. "
            "Run batch_ingest.py first."
        )
        return

    # Embed the test query
    logger.info(f"Query: {query}")
    query_embedding = embed_query(query)
    logger.info(f"Query embedded: {len(query_embedding)} dimensions")

    # Run similarity search
    results = query_collection(
        query_embedding=query_embedding,
        n_results=n_results,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    logger.info(f"\nTop {len(documents)} results:\n")

    for i, (doc, meta, dist) in enumerate(
        zip(documents, metadatas, distances), start=1
    ):
        logger.info(f"Result {i}")
        logger.info(f"  Source   : {meta.get('document_name')}")
        logger.info(f"  Date     : {meta.get('meeting_date')}")
        logger.info(f"  Dept     : {meta.get('department')}")
        logger.info(f"  Distance : {dist:.4f}")
        logger.info(f"  Excerpt  : {doc[:200]}...")
        logger.info("")

    logger.info("Pipeline test complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test the meeting minute chatbot retrieval pipeline."
    )
    parser.add_argument(
        "--query",
        type=str,
        default="What decisions were made in the last meeting?",
        help="Test query to run against the knowledge base",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=5,
        help="Number of results to retrieve (default: 5)",
    )
    args = parser.parse_args()
    run_test(args.query, args.n)