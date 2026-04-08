"""Text cleaning and extraction utilities."""

import re
import unicodedata
from typing import Optional


def clean_text(text: str) -> str:
    """Normalize whitespace and strip control characters.

    - Removes non-printable control characters (keeps newlines, tabs, spaces)
    - Collapses multiple whitespace into single spaces
    - Strips leading/trailing whitespace
    """
    # Remove control characters except newline, tab, space
    cleaned = "".join(
        ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\t\r"
    )
    # Normalize whitespace: collapse runs of spaces/tabs (preserve newlines)
    cleaned = re.sub(r"[^\S\n]+", " ", cleaned)
    # Collapse multiple blank lines into one
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_date_from_text(text: str) -> Optional[str]:
    """Extract a date string from text using common patterns.

    Supports formats like:
    - January 15, 2025
    - Jan 15, 2025
    - 01/15/2025
    - 2025-01-15
    - Q4 2025 / Q1 2024

    Returns the first matched date string, or None.
    """
    patterns = [
        # ISO format: 2025-01-15
        r"\b(\d{4}-\d{2}-\d{2})\b",
        # US format: 01/15/2025
        r"\b(\d{2}/\d{2}/\d{4})\b",
        # Long month: January 15, 2025
        r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b",
        # Short month: Jan 15, 2025
        r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
        # Quarter: Q4 2025
        r"\b(Q[1-4]\s+\d{4})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None
