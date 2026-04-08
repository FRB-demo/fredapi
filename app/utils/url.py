"""URL handling utilities."""

import os
import re
from urllib.parse import unquote, urljoin, urlparse, urlunparse


def extract_filename(url: str) -> str:
    """Extract a clean filename from a URL.

    Examples:
        >>> extract_filename("https://example.com/docs/report.pdf")
        'report.pdf'
        >>> extract_filename("https://example.com/docs/report.pdf?v=2")
        'report.pdf'
    """
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = os.path.basename(path)
    # Remove any remaining query-like fragments
    filename = re.sub(r"[?#].*$", "", filename)
    return filename or "unknown"


def normalize_url(url: str) -> str:
    """Normalize a URL for deduplication.

    - Lowercases the scheme and host
    - Removes default ports (80, 443)
    - Removes trailing slashes from the path
    - Removes fragment identifiers
    - Sorts query parameters
    """
    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()

    # Remove default ports
    port = parsed.port
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None

    netloc = hostname
    if port:
        netloc = f"{hostname}:{port}"

    # Clean path: remove trailing slash (unless it's just "/")
    path = parsed.path.rstrip("/") or "/"

    # Sort query parameters
    query = parsed.query
    if query:
        params = sorted(query.split("&"))
        query = "&".join(params)

    # Drop fragment
    return urlunparse((scheme, netloc, path, parsed.params, query, ""))


def resolve_url(base_url: str, relative_url: str) -> str:
    """Resolve a relative URL against a base URL."""
    return urljoin(base_url, relative_url)
