import chromadb
from typing import List, Optional
from chromadb.config import Settings as ChromaSettings
from backend.app.config import settings
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "meeting_minutes"

# Initialize ChromaDB with persistent local storage
chroma_client = chromadb.PersistentClient(
    path=settings.chroma_persist_path,
    settings=ChromaSettings(anonymized_telemetry=False),
)


def get_or_create_collection():
    """
    Gets the meeting minutes collection or creates it
    if it doesn't exist yet.
    """
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def store_chunks(
    chunks: List[str],
    embeddings: List[List[float]],
    document_id: str,
    document_name: str,
    metadata: dict,
) -> List[str]:
    """
    Stores document chunks with their embeddings and metadata
    into ChromaDB. Returns the list of generated chunk IDs.
    """
    if not chunks or not embeddings:
        logger.warning("No chunks or embeddings to store.")
        return []

    collection = get_or_create_collection()
    chunk_ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"{document_id}_chunk_{i}"
        chunk_ids.append(chunk_id)

        # Flatten metadata for ChromaDB
        # ChromaDB only accepts str, int, float, or bool values
        chunk_metadata = {
            "document_id": str(document_id),
            "document_name": document_name,
            "chunk_index": i,
            "department": metadata.get("department") or "General",
            "meeting_date": (
                metadata["meeting_date"].isoformat()
                if metadata.get("meeting_date") else ""
            ),
            "attendees": ", ".join(metadata.get("attendees") or []),
            "agenda_items": " | ".join(metadata.get("agenda_items") or []),
            "decisions_made": " | ".join(metadata.get("decisions_made") or []),
            "action_items": " | ".join(metadata.get("action_items") or []),
        }
        metadatas.append(chunk_metadata)

    try:
        collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        logger.info(
            f"Stored {len(chunk_ids)} chunks for "
            f"document: {document_name}"
        )

    except Exception as e:
        logger.error(f"Failed to store chunks in ChromaDB: {e}")
        raise

    return chunk_ids


def query_collection(
    query_embedding: List[float],
    n_results: int = 5,
    department_filter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    """
    Runs a similarity search against the ChromaDB collection.
    Applies optional metadata filters for department and date range.
    Returns matched chunks with their metadata and distances.
    """
    collection = get_or_create_collection()

    # Build metadata filter
    filters = []
    if department_filter:
        filters.append({"department": {"$eq": department_filter}})
    if date_from:
        filters.append({"meeting_date": {"$gte": date_from}})
    if date_to:
        filters.append({"meeting_date": {"$lte": date_to}})

    where_filter = None
    if len(filters) == 1:
        where_filter = filters[0]
    elif len(filters) > 1:
        where_filter = {"$and": filters}

    try:
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_params["where"] = where_filter

        results = collection.query(**query_params)
        logger.info(
            f"Query returned {len(results['documents'][0])} chunks"
        )
        return results

    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}")
        raise


def delete_document_chunks(document_id: str) -> None:
    """Deletes all chunks belonging to a specific document."""
    collection = get_or_create_collection()
    try:
        collection.delete(
            where={"document_id": {"$eq": str(document_id)}}
        )
        logger.info(
            f"Deleted all chunks for document_id: {document_id}"
        )
    except Exception as e:
        logger.error(f"Failed to delete chunks for {document_id}: {e}")
        raise


def get_collection_stats() -> dict:
    """Returns basic stats about the ChromaDB collection."""
    collection = get_or_create_collection()
    count = collection.count()
    return {
        "collection_name": COLLECTION_NAME,
        "total_chunks": count,
    }