"""Text chunking with overlap and metadata."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Chunk:
    """A text chunk with associated metadata."""

    text: str
    metadata: Dict = field(default_factory=dict)


def chunk_text(
    text: str,
    max_chars: int = 1000,
    overlap: int = 200,
    metadata: Optional[Dict] = None,
) -> List[Chunk]:
    """Split text into overlapping chunks with metadata attached to each.

    Args:
        text: The full text to split.
        max_chars: Maximum characters per chunk.
        overlap: Number of characters to overlap between consecutive chunks.
        metadata: Base metadata dict to attach to every chunk.

    Returns:
        List of Chunk objects with text and metadata.
    """
    if not text or not text.strip():
        return []

    if metadata is None:
        metadata = {}

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= max_chars:
        raise ValueError("overlap must be less than max_chars")

    chunks: List[Chunk] = []
    text = text.strip()
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + max_chars

        # If this isn't the last chunk, try to break at a sentence or word boundary
        if end < len(text):
            # Try sentence boundary first (., !, ?)
            boundary = _find_boundary(text, start, end)
            if boundary > start:
                end = boundary

        chunk_text_content = text[start:end].strip()

        if chunk_text_content:
            chunk_meta = {**metadata, "chunk_index": chunk_index}
            chunks.append(Chunk(text=chunk_text_content, metadata=chunk_meta))
            chunk_index += 1

        # Move start forward by (end - start - overlap), ensuring progress
        step = max(end - start - overlap, 1)
        start = start + step

    return chunks


def _find_boundary(text: str, start: int, end: int) -> int:
    """Find a good text boundary near `end` for splitting.

    Looks for sentence-ending punctuation first, then word boundaries.
    Returns the position after the boundary character, or `end` if no good boundary found.
    """
    # Search backwards from end for sentence boundaries
    search_start = max(start + (end - start) // 2, start)  # Don't go too far back
    segment = text[search_start:end]

    # Try sentence boundaries
    for char in [".\n", ".\r", ". ", "!\n", "! ", "?\n", "? "]:
        pos = segment.rfind(char)
        if pos >= 0:
            return search_start + pos + len(char)

    # Try newline boundary
    pos = segment.rfind("\n")
    if pos >= 0:
        return search_start + pos + 1

    # Try word boundary (space)
    pos = segment.rfind(" ")
    if pos >= 0:
        return search_start + pos + 1

    return end
