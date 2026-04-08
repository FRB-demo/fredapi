"""Abstract base scraper class for data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

import requests


@dataclass
class ScrapedDocument:
    """Represents a document discovered and downloaded by a scraper."""

    url: str
    source_name: str
    doc_type: str  # "pdf", "html", "article"
    title: str
    date: Optional[str] = None
    local_path: Optional[str] = None
    content: Optional[str] = None


class BaseScraper(ABC):
    """Abstract base class for all data source scrapers."""

    name: str = ""
    display_name: str = ""
    base_url: str = ""
    doc_type: str = "pdf"
    last_error: Optional[str] = None

    @abstractmethod
    def scrape(self) -> List[ScrapedDocument]:
        """Discover and download documents from the source.

        Returns:
            List of ScrapedDocument objects with downloaded content.
        """
        pass

    def health_check(self) -> bool:
        """Check if the source URL is reachable.

        Returns:
            True if the source URL responds successfully.
        """
        try:
            response = requests.head(self.base_url, timeout=10, allow_redirects=True)
            return response.status_code < 400
        except requests.RequestException as e:
            self.last_error = str(e)
            return False

    def _download_file(self, url: str, local_path: str) -> bool:
        """Download a file from URL to local path.

        Returns:
            True if download succeeded.
        """
        try:
            response = requests.get(url, timeout=60, stream=True)
            response.raise_for_status()

            import os
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except requests.RequestException as e:
            self.last_error = f"Download failed for {url}: {e}"
            return False
