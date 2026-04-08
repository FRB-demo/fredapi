"""Component tests for Wells Fargo earnings scraper."""

import pytest
import responses

from app.scrapers.wf_earnings import WFEarningsScraper


@pytest.mark.component
class TestWFEarningsScraper:
    @responses.activate
    def test_finds_pdf_links(self, mock_html_earnings):
        """Scraper should find PDF links from mocked HTML."""
        responses.add(
            responses.GET,
            "https://www.wellsfargo.com/about/investor-relations/quarterly-earnings/",
            body=mock_html_earnings,
            status=200,
        )
        # Mock PDF downloads - use a regex pattern to match any PDF URL
        import re

        responses.add(
            responses.GET,
            re.compile(r".*\.pdf$"),
            body=b"%PDF-1.4 fake pdf content",
            status=200,
        )

        scraper = WFEarningsScraper()
        # Override download path to avoid filesystem issues
        from unittest.mock import patch

        with patch("app.scrapers.wf_earnings.get_settings") as mock_settings:
            mock_settings.return_value.download_path = "/tmp/test_downloads"
            documents = scraper.scrape()

        # The mock HTML has 4 PDF links
        assert len(documents) >= 1
        for doc in documents:
            assert doc.source_name == "wf_earnings"
            assert doc.doc_type == "pdf"
            assert doc.url.endswith(".pdf")

    @responses.activate
    def test_handles_404(self):
        """Scraper should handle 404 gracefully."""
        responses.add(
            responses.GET,
            "https://www.wellsfargo.com/about/investor-relations/quarterly-earnings/",
            status=404,
        )

        scraper = WFEarningsScraper()
        documents = scraper.scrape()
        assert documents == []
        assert scraper.last_error is not None

    @responses.activate
    def test_handles_empty_page(self):
        """Scraper should handle a page with no PDF links."""
        responses.add(
            responses.GET,
            "https://www.wellsfargo.com/about/investor-relations/quarterly-earnings/",
            body="<html><body>No documents available</body></html>",
            status=200,
        )

        scraper = WFEarningsScraper()
        documents = scraper.scrape()
        assert documents == []

    @responses.activate
    def test_health_check_success(self):
        """Health check should return True when URL is reachable."""
        responses.add(
            responses.HEAD,
            "https://www.wellsfargo.com/about/investor-relations/quarterly-earnings/",
            status=200,
        )

        scraper = WFEarningsScraper()
        assert scraper.health_check() is True

    @responses.activate
    def test_health_check_failure(self):
        """Health check should return False when URL is unreachable."""
        responses.add(
            responses.HEAD,
            "https://www.wellsfargo.com/about/investor-relations/quarterly-earnings/",
            status=500,
        )

        scraper = WFEarningsScraper()
        assert scraper.health_check() is False

    def test_extract_quarter_date(self):
        """Should extract quarter date from title."""
        scraper = WFEarningsScraper()
        assert scraper._extract_quarter_date("Q4 2025 Earnings Report") == "Q4 2025"
        assert scraper._extract_quarter_date("First Quarter 2025 Report") == "First Quarter 2025"
        assert scraper._extract_quarter_date("Some random title") is None
