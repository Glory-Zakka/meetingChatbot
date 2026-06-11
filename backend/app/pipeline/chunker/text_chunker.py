from typing import List
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

# Chunk configuration
CHUNK_SIZE = 512    # characters per chunk
CHUNK_OVERLAP = 80  # characters of overlap between chunks


def chunk_text(
    raw_text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> List[str]:
    """
    Splits raw text into overlapping chunks of roughly chunk_size characters.
    Tries to split on paragraph boundaries where possible to avoid
    cutting sentences mid-way.
    """
    if not raw_text or not raw_text.strip():
        return []

    # Split into paragraphs first
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # If adding this paragraph keeps us under chunk_size, add it
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            # Save the current chunk if it has content
            if current_chunk:
                chunks.append(current_chunk.strip())
                # Start next chunk with overlap from end of previous chunk
                current_chunk = current_chunk[-overlap:] + "\n\n" + para
            else:
                # Paragraph itself is larger than chunk_size — split by words
                words = para.split()
                temp = ""
                for word in words:
                    if len(temp) + len(word) + 1 <= chunk_size:
                        temp += (" " if temp else "") + word
                    else:
                        if temp:
                            chunks.append(temp.strip())
                            temp = temp[-overlap:] + " " + word
                        else:
                            temp = word
                current_chunk = temp

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Remove duplicates while preserving order
    seen = set()
    unique_chunks = []
    for chunk in chunks:
        if chunk not in seen:
            seen.add(chunk)
            unique_chunks.append(chunk)

    logger.info(
        f"Chunked text into {len(unique_chunks)} chunks "
        f"(size={chunk_size}, overlap={overlap})"
    )

    return unique_chunks


def chunk_by_section(sections: List[dict]) -> List[str]:
    """
    Alternative chunker for DOCX files that have clear headings.
    Each section heading + content is chunked independently.
    This preserves context better for structured meeting minutes.
    """
    chunks = []

    for section in sections:
        heading = section.get("heading", "")
        content = "\n".join(section.get("content", []))
        section_text = f"{heading}\n{content}" if heading else content

        if section_text.strip():
            section_chunks = chunk_text(section_text)
            chunks.extend(section_chunks)

    logger.info(
        f"Section-based chunking produced {len(chunks)} chunks"
    )

    return chunks