from typing import List
from sentence_transformers import SentenceTransformer
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

# Free local embedding model — no API key needed
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Load the model once when the module is imported
# It will download automatically on first run (~90MB)
model = SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generates vector embeddings for a list of text chunks.
    Runs locally using sentence-transformers — no API cost.
    Returns a list of embedding vectors, one per input text.
    """
    if not texts:
        return []

    try:
        logger.info(f"Embedding {len(texts)} chunks locally...")
        embeddings = model.encode(texts, show_progress_bar=True)
        result = embeddings.tolist()
        logger.info(f"Embeddings generated: {len(result)} vectors")
        return result

    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise


def embed_query(query: str) -> List[float]:
    """
    Embeds a single query string for similarity search.
    Used at query time when a staff member asks a question.
    """
    try:
        logger.info(f"Embedding query: {query[:60]}...")
        embedding = model.encode([query])
        return embedding[0].tolist()

    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        raise