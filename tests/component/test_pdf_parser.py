"""Component tests for PDF parser."""

import pytest

from app.processing.pdf_parser import PDFParseError, parse_pdf


@pytest.mark.component
class TestPDFParser:
    def test_parse_sample_pdf(self, sample_earnings_pdf):
        """Should extract text from a valid PDF."""
        text = parse_pdf(sample_earnings_pdf)
        assert len(text) > 0
        assert "Wells Fargo" in text

    def test_corrupted_pdf_raises_error(self, corrupted_pdf):
        """Should raise PDFParseError for corrupted PDF."""
        with pytest.raises(PDFParseError):
            parse_pdf(corrupted_pdf)

    def test_nonexistent_file_raises_error(self):
        """Should raise PDFParseError for missing file."""
        with pytest.raises(PDFParseError):
            parse_pdf("/nonexistent/path/file.pdf")

    def test_extracted_text_contains_known_content(self, sample_earnings_pdf):
        """Extracted text should contain known content from fixture."""
        text = parse_pdf(sample_earnings_pdf)
        # Our sample PDF should contain these strings
        assert "Q4 2025" in text or "net income" in text.lower()
