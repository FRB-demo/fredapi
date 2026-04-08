"""Wells Fargo Annual Reports scraper."""

import os
import re
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.config import get_settings
from app.scrapers.base_scraper import BaseScraper, ScrapedDocument
from app.utils.url import extract_filename, normalize_url


class WFAnnualReportsScraper(BaseScraper):
    """Scraper for Wells Fargo annual reports."""

    name = "wf_annual_reports"
    display_name = "Wells Fargo Annual Reports"
    base_url = "https://www.wellsfargo.com/about/investor-relations/annual-reports/"
    doc_type = "pdf"

    def scrape(self) -> List[ScrapedDocument]:
        """Scrape Wells Fargo annual reports page for PDF links."""
        documents: List[ScrapedDocument] = []

        try:
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            self.last_error = f"Failed to fetch annual reports page: {e}"
            return documents

        soup = BeautifulSoup(response.text, "lxml")
        pdf_links = self._find_pdf_links(soup)

        settings = get_settings()
        download_dir = os.path.join(settings.download_path, self.name)

        for url, title in pdf_links:
            filename = extract_filename(url)
            local_path = os.path.join(download_dir, filename)

            doc = ScrapedDocument(
                url=url,
                source_name=self.name,
                doc_type=self.doc_type,
                title=title,
                date=self._extract_year(title),
                local_path=local_path,
            )

            if self._download_file(url, local_path):
                documents.append(doc)

        return documents

    def _find_pdf_links(self, soup: BeautifulSoup) -> List[tuple]:
        """Extract PDF links and titles from the page."""
        pdf_links = []
        seen_urls = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if not href.lower().endswith(".pdf"):
                continue

            absolute_url = urljoin(self.base_url, href)
            normalized = normalize_url(absolute_url)

            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)

            title = link.get_text(strip=True)
            if not title:
                title = extract_filename(href)

            pdf_links.append((absolute_url, title))

        return pdf_links

    def _extract_year(self, title: str) -> str | None:
        """Try to extract year from title text."""
        match = re.search(r"\b(20\d{2})\b", title)
        if match:
            return match.group(1)
        return None
