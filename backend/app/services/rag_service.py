from backend.app.pipeline.embedder.openai_embedder import embed_query
from backend.app.pipeline.vector_store.chroma_store import query_collection
from backend.app.services.llm_service import generate_answer
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def ask_question(
    question: str,
    n_results: int = 5,
    department_filter: str = None,
    date_from: str = None,
    date_to: str = None,
) -> dict:
    """
    Master RAG function. Orchestrates the full query pipeline:
    embed question → retrieve chunks → generate answer.

    Args:
        question: The staff member's natural language question
        n_results: Number of chunks to retrieve from ChromaDB
        department_filter: Optional department to filter results by
        date_from: Optional start date filter (ISO format)
        date_to: Optional end date filter (ISO format)

    Returns:
        Dict with answer, sources, and retrieved chunks
    """
    logger.info(f"Processing question: {question[:80]}...")

    # ── STEP 1: Embed the question ──────────────────────────────────
    logger.info("Step 1: Embedding question...")
    query_embedding = embed_query(question)

    # ── STEP 2: Retrieve relevant chunks from ChromaDB ──────────────
    logger.info("Step 2: Retrieving relevant chunks...")
    results = query_collection(
        query_embedding=query_embedding,
        n_results=n_results,
        department_filter=department_filter,
        date_from=date_from,
        date_to=date_to,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        logger.warning("No relevant chunks found for question.")
        return {
            "question": question,
            "answer": (
                "I could not find any relevant information in the "
                "available meeting records for your question."
            ),
            "sources": [],
            "chunks_retrieved": 0,
        }

    # Build structured chunk list for the LLM
    context_chunks = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        context_chunks.append({
            "text": doc,
            "metadata": meta,
            "distance": dist,
        })

    logger.info(f"Retrieved {len(context_chunks)} relevant chunks")

    # ── STEP 3: Generate answer using LLM ───────────────────────────
    logger.info("Step 3: Generating answer...")
    llm_response = generate_answer(
        question=question,
        context_chunks=context_chunks,
    )

    return {
        "question": question,
        "answer": llm_response["answer"],
        "sources": llm_response["sources"],
        "chunks_retrieved": len(context_chunks),
    }