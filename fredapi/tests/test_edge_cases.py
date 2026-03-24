"""Edge case and error handling tests for fredapi."""

import io
import math
import sys
import xml.etree.ElementTree as ET

import pandas as pd
import pytest

from fredapi import Fred
import fredapi.fred
from fredapi.tests.conftest import (
    make_error_xml,
    make_observations_xml,
    make_search_xml,
    make_series_info_xml,
    set_mock_response,
)


class TestEmptyResponses:
    """Tests for empty or missing data."""

    def test_series_no_observations_empty_xml(self, fred, mock_urlopen):
        """Series with no observations (empty XML) returns empty Series."""
        xml = make_observations_xml([])
        set_mock_response(mock_urlopen, xml)
        result = fred.get_series("EMPTY")

        assert isinstance(result, pd.Series)
        assert len(result) == 0

    def test_series_info_empty_raises(self, fred, mock_urlopen):
        """get_series_info with empty response raises ValueError."""
        xml = '<?xml version="1.0" encoding="utf-8" ?>\n<seriess></seriess>'
        set_mock_response(mock_urlopen, xml)

        with pytest.raises(ValueError, match="No info exists for series id"):
            fred.get_series_info("NONEXISTENT")


class TestNaNHandling:
    """Tests for missing/NaN value handling."""

    def test_single_nan_value(self, fred, mock_urlopen):
        """value='.' should be converted to float NaN."""
        xml = make_observations_xml([
            {"date": "2023-01-01", "value": "."},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred.get_series("TEST")

        assert len(result) == 1
        assert math.isnan(result.iloc[0])

    def test_mixed_nan_and_values(self, fred, mock_urlopen):
        """Mix of '.' and numeric values handled correctly."""
        xml = make_observations_xml([
            {"date": "2023-01-01", "value": "100.5"},
            {"date": "2023-02-01", "value": "."},
            {"date": "2023-03-01", "value": "."},
            {"date": "2023-04-01", "value": "103.2"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred.get_series("TEST")

        assert result.iloc[0] == 100.5
        assert math.isnan(result.iloc[1])
        assert math.isnan(result.iloc[2])
        assert result.iloc[3] == 103.2

    def test_all_nan_values(self, fred, mock_urlopen):
        """All '.' values should produce a Series of all NaN."""
        xml = make_observations_xml([
            {"date": "2023-01-01", "value": "."},
            {"date": "2023-02-01", "value": "."},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred.get_series("TEST")

        assert len(result) == 2
        assert all(math.isnan(v) for v in result.values)

    def test_nan_in_all_releases(self, fred, mock_urlopen):
        """NaN values in all_releases should also be converted."""
        xml = make_observations_xml([
            {"date": "2023-01-01", "realtime_start": "2023-04-01", "value": "."},
            {"date": "2023-01-01", "realtime_start": "2023-05-01", "value": "200.0"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred.get_series_all_releases("TEST")

        # pd.DataFrame.T may coerce NaN to NaT when mixed with datetime columns;
        # use pd.isna which handles both NaN and NaT.
        assert pd.isna(result.iloc[0]["value"])
        assert result.iloc[1]["value"] == 200.0


class TestLargeDatasets:
    """Tests for large data responses."""

    def test_long_date_range(self, fred, mock_urlopen):
        """Generate 600+ monthly observations and verify all are returned."""
        observations = []
        start_year = 1970
        for i in range(620):
            year = start_year + i // 12
            month = (i % 12) + 1
            observations.append({
                "date": f"{year:04d}-{month:02d}-01",
                "value": str(100.0 + i * 0.1),
            })

        xml = make_observations_xml(observations)
        set_mock_response(mock_urlopen, xml)
        result = fred.get_series("LONG")

        assert len(result) == 620
        assert isinstance(result.index, pd.DatetimeIndex)


class TestUnicode:
    """Tests for unicode characters in data."""

    def test_unicode_in_series_title(self, fred, mock_urlopen):
        """Series info with unicode characters in title should work."""
        attrs = {
            "id": "UNICODE",
            "realtime_start": "2024-01-01",
            "realtime_end": "2024-01-01",
            "title": "Consumer Price Index: All Items \u2014 Euro Area",
            "observation_start": "2000-01-01",
            "observation_end": "2024-01-01",
            "frequency": "Monthly",
            "frequency_short": "M",
            "units": "Index 2015=100",
            "units_short": "Idx",
            "seasonal_adjustment": "Not Seasonally Adjusted",
            "seasonal_adjustment_short": "NSA",
            "last_updated": "2024-01-01 08:00:00-06",
            "popularity": "50",
            "notes": "Data from Eurostat. Harmonised Index \u00e9l\u00e8ves.",
        }
        xml = make_series_info_xml(attrs)
        set_mock_response(mock_urlopen, xml)
        result = fred.get_series_info("UNICODE")

        assert "\u2014" in result["title"]
        assert "\u00e9" in result["notes"]

    def test_unicode_in_search_results(self, fred, mock_urlopen):
        """Search results with unicode characters should work."""
        series = [
            {"id": "UNI1", "title": "Gro\u00df domestic product \u2013 Germany"},
        ]
        xml = make_search_xml(series)
        set_mock_response(mock_urlopen, xml)
        result = fred.search("German GDP")

        assert "\u2013" in result.loc["UNI1", "title"]


class TestHTTPErrors:
    """Tests for HTTP error handling."""

    def test_http_error_400_raises_valueerror(self, fred, mock_urlopen):
        """HTTP 400 error should raise ValueError with message from XML."""
        error_xml = make_error_xml(400, "Bad Request. The series does not exist.")
        fp = io.StringIO(error_xml)
        exc = fredapi.fred.HTTPError(
            "https://api.stlouisfed.org/fred/test", 400, "Bad Request", {}, fp
        )
        mock_urlopen.side_effect = exc

        with pytest.raises(ValueError, match="Bad Request"):
            fred.get_series("INVALID")

    def test_http_error_403_invalid_api_key(self, fred, mock_urlopen):
        """HTTP 403 with invalid API key should raise ValueError."""
        error_xml = make_error_xml(403, "Bad Request. API key is invalid.")
        fp = io.StringIO(error_xml)
        exc = fredapi.fred.HTTPError(
            "https://api.stlouisfed.org/fred/test", 403, "Forbidden", {}, fp
        )
        mock_urlopen.side_effect = exc

        with pytest.raises(ValueError, match="API key"):
            fred.get_series("GDP")

    def test_http_error_429_rate_limiting(self, fred, mock_urlopen):
        """HTTP 429 rate limiting should raise ValueError."""
        error_xml = make_error_xml(429, "Too Many Requests. API rate limit exceeded.")
        fp = io.StringIO(error_xml)
        exc = fredapi.fred.HTTPError(
            "https://api.stlouisfed.org/fred/test", 429, "Too Many Requests", {}, fp
        )
        mock_urlopen.side_effect = exc

        with pytest.raises(ValueError, match="Too Many Requests"):
            fred.get_series("GDP")

    def test_http_error_401_unauthorized(self, fred, mock_urlopen):
        """HTTP 401 unauthorized should raise ValueError."""
        error_xml = make_error_xml(401, "Unauthorized. API key missing or invalid.")
        fp = io.StringIO(error_xml)
        exc = fredapi.fred.HTTPError(
            "https://api.stlouisfed.org/fred/test", 401, "Unauthorized", {}, fp
        )
        mock_urlopen.side_effect = exc

        with pytest.raises(ValueError, match="Unauthorized"):
            fred.get_series("GDP")


class TestNetworkErrors:
    """Tests for network-level errors."""

    def test_urlopen_timeout(self, fred, mock_urlopen):
        """Network timeout should propagate as an error."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("timed out")

        with pytest.raises(URLError):
            fred.get_series("GDP")

    def test_urlopen_connection_refused(self, fred, mock_urlopen):
        """Connection refused should propagate as URLError."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Connection refused")

        with pytest.raises(URLError):
            fred.get_series("GDP")


class TestMalformedResponses:
    """Tests for malformed XML responses."""

    def test_malformed_xml_raises(self, fred, mock_urlopen):
        """Malformed XML should raise ET.ParseError."""
        mock_urlopen.return_value.read.return_value = "<not valid xml><unclosed"

        with pytest.raises(ET.ParseError):
            fred.get_series("GDP")

    def test_completely_empty_response(self, fred, mock_urlopen):
        """Completely empty response should raise an error."""
        mock_urlopen.return_value.read.return_value = ""

        with pytest.raises(ET.ParseError):
            fred.get_series("GDP")


class TestAPIKeyHandling:
    """Tests for API key configuration."""

    def test_empty_string_api_key_accepted(self):
        """Empty string API key is accepted (no ValueError on init)."""
        # Fred.__init__ only raises if api_key is None, not empty string
        fred_instance = Fred(api_key="")
        assert fred_instance.api_key == ""

    def test_no_api_key_raises(self):
        """No API key provided at all raises ValueError."""
        # Clear env var if set
        import os
        original = os.environ.pop("FRED_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="You need to set a valid API key"):
                Fred()
        finally:
            if original is not None:
                os.environ["FRED_API_KEY"] = original

    def test_api_key_from_env(self):
        """API key can be read from FRED_API_KEY environment variable."""
        import os
        original = os.environ.get("FRED_API_KEY")
        try:
            os.environ["FRED_API_KEY"] = "env_test_key"
            fred_instance = Fred()
            assert fred_instance.api_key == "env_test_key"
        finally:
            if original is not None:
                os.environ["FRED_API_KEY"] = original
            else:
                os.environ.pop("FRED_API_KEY", None)

    def test_api_key_from_file(self, tmp_path):
        """API key can be read from a file."""
        key_file = tmp_path / "api_key.txt"
        key_file.write_text("file_test_key\n")
        fred_instance = Fred(api_key_file=str(key_file))
        assert fred_instance.api_key == "file_test_key"

    def test_api_key_explicit_takes_precedence(self):
        """Explicit api_key parameter takes precedence over env var."""
        import os
        original = os.environ.get("FRED_API_KEY")
        try:
            os.environ["FRED_API_KEY"] = "env_key"
            fred_instance = Fred(api_key="explicit_key")
            assert fred_instance.api_key == "explicit_key"
        finally:
            if original is not None:
                os.environ["FRED_API_KEY"] = original
            else:
                os.environ.pop("FRED_API_KEY", None)


class TestInvalidDateArgs:
    """Tests for invalid date arguments."""

    def test_invalid_observation_start_raises(self, fred, mock_urlopen):
        """Invalid observation_start string raises ValueError."""
        with pytest.raises(Exception):
            fred.get_series("GDP", observation_start="not-a-date")

    def test_invalid_observation_end_raises(self, fred, mock_urlopen):
        """Invalid observation_end string raises ValueError."""
        with pytest.raises(Exception):
            fred.get_series("GDP", observation_end="not-a-date")
