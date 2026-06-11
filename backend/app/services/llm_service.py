from groq import Groq
from backend.app.config import settings
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

client = Groq(api_key=settings.groq_api_key)

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an intelligent assistant for an organization's 
meeting records. Your job is to answer staff questions based strictly 
on the meeting minutes provided to you as context.

Follow these rules without exception:
1. Answer ONLY based on the provided meeting minutes context.
2. Never use your general knowledge to fill gaps — if it's not in 
   the context, say so clearly.
3. Always mention which meeting document your answer comes from, 
   including the document name and date.
4. If the answer is not found in any of the provided context, respond 
   with: "I could not find information about this in the available 
   meeting records. Please check with the relevant department or 
   administrator."
5. Be concise and professional in your responses.
6. If multiple meetings discussed the same topic, summarize all 
   relevant points and cite each source.
"""


def generate_answer(question: str, context_chunks: list) -> dict:
    """
    Generates an answer to a question based on retrieved context chunks.
    
    Args:
        question: The staff member's question
        context_chunks: List of dicts with 'text' and 'metadata' keys
    
    Returns:
        Dict with 'answer' and 'sources' keys
    """
    if not context_chunks:
        return {
            "answer": (
                "I could not find any relevant information in the "
                "available meeting records for your question."
            ),
            "sources": [],
        }

    # Build context string from retrieved chunks
    context_parts = []
    sources = []

    for i, chunk in enumerate(context_chunks, start=1):
        text = chunk.get("text", "")
        metadata = chunk.get("metadata", {})
        doc_name = metadata.get("document_name", "Unknown document")
        meeting_date = metadata.get("meeting_date", "Unknown date")
        department = metadata.get("department", "")

        context_parts.append(
            f"[Source {i}] Document: {doc_name} | "
            f"Date: {meeting_date} | Department: {department}\n"
            f"{text}"
        )

        # Collect unique sources for citation
        source_entry = {
            "document_name": doc_name,
            "meeting_date": meeting_date,
            "department": department,
        }
        if source_entry not in sources:
            sources.append(source_entry)

    context_text = "\n\n---\n\n".join(context_parts)

    # Build the user message
    user_message = (
        f"Based on the following meeting minutes, please answer "
        f"this question:\n\n"
        f"Question: {question}\n\n"
        f"Meeting Minutes Context:\n{context_text}"
    )

    logger.info(
        f"Sending query to Groq | model={MODEL} | "
        f"chunks={len(context_chunks)} | "
        f"question={question[:60]}..."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,  # Low temperature = more factual, less creative
            max_tokens=1024,
        )

        answer = response.choices[0].message.content
        logger.info("Answer generated successfully")

        return {
            "answer": answer,
            "sources": sources,
        }

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise