"""Unit tests for utility modules."""

import pytest

from app.utils.text import clean_text, extract_date_from_text
from app.utils.url import extract_filename, normalize_url


@pytest.mark.unit
class TestCleanText:
    def test_normalizes_whitespace(self):
        assert clean_text("hello   world") == "hello world"

    def test_strips_control_characters(self):
        text = "hello\x00world\x01test"
        result = clean_text(text)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "hello" in result
        assert "world" in result

    def test_preserves_newlines(self):
        result = clean_text("line1\nline2")
        assert "line1\nline2" == result

    def test_collapses_multiple_blank_lines(self):
        result = clean_text("line1\n\n\n\n\nline2")
        assert result == "line1\n\nline2"

    def test_strips_leading_trailing(self):
        assert clean_text("  hello  ") == "hello"

    def test_empty_string(self):
        assert clean_text("") == ""


@pytest.mark.unit
class TestExtractDate:
    def test_iso_format(self):
        assert extract_date_from_text("Report dated 2025-01-15 was released") == "2025-01-15"

    def test_us_format(self):
        assert extract_date_from_text("Report dated 01/15/2025") == "01/15/2025"

    def test_long_month(self):
        result = extract_date_from_text("Published January 15, 2025")
        assert result == "January 15, 2025"

    def test_short_month(self):
        result = extract_date_from_text("Published Jan 15, 2025")
        assert "Jan" in result
        assert "2025" in result

    def test_quarter(self):
        assert extract_date_from_text("Results for Q4 2025") == "Q4 2025"

    def test_no_date(self):
        assert extract_date_from_text("No date information here") is None


@pytest.mark.unit
class TestExtractFilename:
    def test_simple_url(self):
        assert extract_filename("https://example.com/docs/report.pdf") == "report.pdf"

    def test_url_with_query(self):
        assert extract_filename("https://example.com/docs/report.pdf?v=2") == "report.pdf"

    def test_url_with_fragment(self):
        assert extract_filename("https://example.com/docs/report.pdf#page=5") == "report.pdf"

    def test_encoded_url(self):
        assert extract_filename("https://example.com/docs/my%20report.pdf") == "my report.pdf"

    def test_no_filename(self):
        assert extract_filename("https://example.com/") == "unknown"


@pytest.mark.unit
class TestNormalizeUrl:
    def test_lowercases_scheme_and_host(self):
        result = normalize_url("HTTPS://EXAMPLE.COM/path")
        assert result.startswith("https://example.com")

    def test_removes_default_port(self):
        result = normalize_url("https://example.com:443/path")
        assert ":443" not in result

    def test_keeps_non_default_port(self):
        result = normalize_url("https://example.com:8080/path")
        assert ":8080" in result

    def test_removes_trailing_slash(self):
        result = normalize_url("https://example.com/path/")
        assert result.endswith("/path")

    def test_removes_fragment(self):
        result = normalize_url("https://example.com/path#section")
        assert "#section" not in result

    def test_sorts_query_params(self):
        result = normalize_url("https://example.com/path?b=2&a=1")
        assert "a=1&b=2" in result
