"""Comprehensive pytest-based test suite for fredapi.Fred.

All tests use mocks exclusively -- no real FRED API key is required.
"""

import math
from datetime import datetime
from unittest import mock

import pandas as pd
import pytest

import fredapi
import fredapi.fred
from fredapi import Fred

from tests.conftest import (
    make_observations_xml,
    make_series_info_xml,
    make_empty_series_info_xml,
    make_search_xml,
    make_empty_search_xml,
    make_vintage_dates_xml,
    make_error_xml,
    set_mock_response,
    set_mock_http_error,
)


# =========================================================================
# Initialization / API key tests
# =========================================================================

class TestFredInit:
    """Tests for Fred.__init__ and API-key resolution."""

    def test_init_with_api_key(self):
        fred = Fred(api_key="my_key")
        assert fred.api_key == "my_key"

    def test_init_with_api_key_file(self, tmp_path):
        key_file = tmp_path / "key.txt"
        key_file.write_text("file_key_123\n")
        fred = Fred(api_key_file=str(key_file))
        assert fred.api_key == "file_key_123"

    def test_init_with_env_var(self, monkeypatch):
        monkeypatch.setenv("FRED_API_KEY", "env_key_456")
        fred = Fred()
        assert fred.api_key == "env_key_456"

    def test_init_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        with pytest.raises(ValueError, match="You need to set a valid API key"):
            Fred()

    def test_init_api_key_precedence_over_env(self, monkeypatch):
        monkeypatch.setenv("FRED_API_KEY", "env_key")
        fred = Fred(api_key="direct_key")
        assert fred.api_key == "direct_key"

    def test_init_with_proxies(self):
        proxies = {"http": "http://proxy:8080", "https": "https://proxy:8443"}
        fred = Fred(api_key="k", proxies=proxies)
        assert fred.proxies == proxies

    def test_init_proxies_from_env(self, monkeypatch):
        monkeypatch.setenv("HTTP_PROXY", "http://envproxy:80")
        monkeypatch.setenv("HTTPS_PROXY", "https://envproxy:443")
        fred = Fred(api_key="k")
        assert fred.proxies == {"http": "http://envproxy:80", "https": "https://envproxy:443"}

    def test_init_no_proxies(self, monkeypatch):
        monkeypatch.delenv("HTTP_PROXY", raising=False)
        monkeypatch.delenv("HTTPS_PROXY", raising=False)
        fred = Fred(api_key="k")
        assert fred.proxies is None


# =========================================================================
# _parse helper
# =========================================================================

class TestParse:
    """Tests for Fred._parse date parsing helper."""

    def test_parse_standard_date(self, fred_client):
        result = fred_client._parse("2024-03-15")
        assert result == datetime(2024, 3, 15)

    def test_parse_custom_format(self, fred_client):
        result = fred_client._parse("03/15/2024", format="%m/%d/%Y")
        assert result == datetime(2024, 3, 15)


# =========================================================================
# get_series
# =========================================================================

class TestGetSeries:
    """Tests for Fred.get_series."""

    def test_normal_response(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "100.5"},
            {"date": "2024-02-01", "value": "101.2"},
            {"date": "2024-03-01", "value": "102.0"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series("TEST")
        assert len(result) == 3
        assert result.iloc[0] == 100.5
        assert result.iloc[2] == 102.0

    def test_empty_series(self, fred_client, mock_urlopen):
        xml = make_observations_xml([])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series("EMPTY")
        assert len(result) == 0
        assert isinstance(result, pd.Series)

    def test_nan_values(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "100.0"},
            {"date": "2024-02-01", "value": "."},
            {"date": "2024-03-01", "value": "102.0"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series("NANTEST")
        assert result.iloc[0] == 100.0
        assert math.isnan(result.iloc[1])
        assert result.iloc[2] == 102.0

    def test_observation_start_end(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-15", "value": "50.0"},
        ])
        set_mock_response(mock_urlopen, xml)
        fred_client.get_series(
            "TEST",
            observation_start="2024-01-01",
            observation_end="2024-01-31",
        )
        called_url = mock_urlopen.call_args[0][0]
        assert "observation_start=2024-01-01" in called_url
        assert "observation_end=2024-01-31" in called_url

    def test_kwargs_passed_to_url(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "10.0"},
        ])
        set_mock_response(mock_urlopen, xml)
        fred_client.get_series("TEST", units="chg", frequency="m")
        called_url = mock_urlopen.call_args[0][0]
        assert "units=chg" in called_url
        assert "frequency=m" in called_url

    def test_url_contains_series_id_and_api_key(self, fred_client, mock_urlopen):
        xml = make_observations_xml([{"date": "2024-01-01", "value": "1.0"}])
        set_mock_response(mock_urlopen, xml)
        fred_client.get_series("GDP")
        called_url = mock_urlopen.call_args[0][0]
        assert "series_id=GDP" in called_url
        assert "api_key=test_api_key_12345" in called_url

    def test_invalid_observation_start_raises(self, fred_client, mock_urlopen):
        with pytest.raises(Exception):
            fred_client.get_series("TEST", observation_start="not-a-date")


# =========================================================================
# get_series_info
# =========================================================================

class TestGetSeriesInfo:
    """Tests for Fred.get_series_info."""

    def test_normal_response(self, fred_client, mock_urlopen):
        xml = make_series_info_xml({
            "id": "CPIAUCSL",
            "title": "Consumer Price Index",
            "frequency": "Monthly",
            "frequency_short": "M",
            "units": "Index 1982-1984=100",
            "units_short": "Index",
            "seasonal_adjustment": "Seasonally Adjusted",
            "seasonal_adjustment_short": "SA",
            "observation_start": "1947-01-01",
            "observation_end": "2024-01-01",
            "last_updated": "2024-02-13 07:41:05-06",
            "popularity": "94",
            "notes": "Test CPI notes",
        })
        set_mock_response(mock_urlopen, xml)
        info = fred_client.get_series_info("CPIAUCSL")
        assert isinstance(info, pd.Series)
        assert info["id"] == "CPIAUCSL"
        assert info["title"] == "Consumer Price Index"
        assert info["frequency"] == "Monthly"

    def test_minimal_fields(self, fred_client, mock_urlopen):
        xml = make_series_info_xml({"id": "MINI", "title": "Minimal"})
        set_mock_response(mock_urlopen, xml)
        info = fred_client.get_series_info("MINI")
        assert info["id"] == "MINI"
        assert info["title"] == "Minimal"

    def test_empty_series_info_raises(self, fred_client, mock_urlopen):
        xml = make_empty_series_info_xml()
        set_mock_response(mock_urlopen, xml)
        with pytest.raises(ValueError, match="No info exists for series id"):
            fred_client.get_series_info("INVALID")

    def test_http_400_invalid_series(self, fred_client, mock_urlopen):
        error_msg = "Bad Request.  The series does not exist."
        error_xml = make_error_xml(400, error_msg)
        url = f"{Fred.root_url}/series?series_id=INVALID&api_key=test_api_key_12345"
        set_mock_http_error(mock_urlopen, url, 400, error_xml)
        with pytest.raises(ValueError, match=error_msg):
            fred_client.get_series_info("INVALID")


# =========================================================================
# get_series_latest_release
# =========================================================================

class TestGetSeriesLatestRelease:
    """Tests for Fred.get_series_latest_release (delegates to get_series)."""

    def test_delegates_to_get_series(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "200.0"},
            {"date": "2024-02-01", "value": "201.0"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series_latest_release("TEST")
        assert len(result) == 2
        assert result.iloc[0] == 200.0


# =========================================================================
# get_series_all_releases
# =========================================================================

class TestGetSeriesAllReleases:
    """Tests for Fred.get_series_all_releases."""

    def test_normal_response_with_revisions(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "100.0", "realtime_start": "2024-01-30"},
            {"date": "2024-01-01", "value": "100.5", "realtime_start": "2024-02-28"},
            {"date": "2024-01-01", "value": "101.0", "realtime_start": "2024-03-27"},
            {"date": "2024-04-01", "value": "105.0", "realtime_start": "2024-04-30"},
        ])
        set_mock_response(mock_urlopen, xml)
        df = fred_client.get_series_all_releases("GDP")
        assert isinstance(df, pd.DataFrame)
        assert "date" in df.columns
        assert "realtime_start" in df.columns
        assert "value" in df.columns
        assert len(df) == 4

    def test_custom_realtime_params(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "50.0", "realtime_start": "2024-02-01"},
        ])
        set_mock_response(mock_urlopen, xml)
        fred_client.get_series_all_releases(
            "TEST", realtime_start="2024-01-01", realtime_end="2024-06-30"
        )
        called_url = mock_urlopen.call_args[0][0]
        assert "realtime_start=2024-01-01" in called_url
        assert "realtime_end=2024-06-30" in called_url

    def test_default_realtime_params(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "50.0", "realtime_start": "2024-02-01"},
        ])
        set_mock_response(mock_urlopen, xml)
        fred_client.get_series_all_releases("TEST")
        called_url = mock_urlopen.call_args[0][0]
        assert "realtime_start=1776-07-04" in called_url
        assert "realtime_end=9999-12-31" in called_url

    def test_empty_response(self, fred_client, mock_urlopen):
        xml = make_observations_xml([])
        set_mock_response(mock_urlopen, xml)
        df = fred_client.get_series_all_releases("EMPTY")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_nan_values_in_releases(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": ".", "realtime_start": "2024-01-30"},
            {"date": "2024-01-01", "value": "100.0", "realtime_start": "2024-02-28"},
        ])
        set_mock_response(mock_urlopen, xml)
        df = fred_client.get_series_all_releases("TEST")
        assert pd.isna(df.iloc[0]["value"])
        assert df.iloc[1]["value"] == 100.0


# =========================================================================
# get_series_first_release
# =========================================================================

class TestGetSeriesFirstRelease:
    """Tests for Fred.get_series_first_release."""

    def test_returns_first_release_per_date(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "100.0", "realtime_start": "2024-01-30"},
            {"date": "2024-01-01", "value": "100.5", "realtime_start": "2024-02-28"},
            {"date": "2024-04-01", "value": "105.0", "realtime_start": "2024-04-30"},
            {"date": "2024-04-01", "value": "106.0", "realtime_start": "2024-05-30"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series_first_release("GDP")
        # Should only have one entry per date (first release)
        assert len(result) == 2
        assert result.iloc[0] == 100.0  # first release for 2024-01-01
        assert result.iloc[1] == 105.0  # first release for 2024-04-01

    def test_single_release_per_date(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "100.0", "realtime_start": "2024-01-30"},
            {"date": "2024-02-01", "value": "101.0", "realtime_start": "2024-02-28"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series_first_release("TEST")
        assert len(result) == 2
        assert result.iloc[0] == 100.0
        assert result.iloc[1] == 101.0


# =========================================================================
# get_series_as_of_date
# =========================================================================

class TestGetSeriesAsOfDate:
    """Tests for Fred.get_series_as_of_date."""

    def test_filters_by_as_of_date(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "100.0", "realtime_start": "2024-01-30"},
            {"date": "2024-01-01", "value": "100.5", "realtime_start": "2024-02-28"},
            {"date": "2024-01-01", "value": "101.0", "realtime_start": "2024-03-27"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series_as_of_date("GDP", "2024-02-28")
        # Should include entries with realtime_start <= 2024-02-28
        assert len(result) == 2

    def test_as_of_date_string_parsing(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "100.0", "realtime_start": "2024-01-30"},
            {"date": "2024-01-01", "value": "100.5", "realtime_start": "2024-06-15"},
        ])
        set_mock_response(mock_urlopen, xml)
        # Use a different date format string
        result = fred_client.get_series_as_of_date("GDP", "3/1/2024")
        assert len(result) == 1

    def test_as_of_date_includes_all(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-01-01", "value": "100.0", "realtime_start": "2024-01-01"},
            {"date": "2024-02-01", "value": "101.0", "realtime_start": "2024-02-01"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series_as_of_date("TEST", "2025-01-01")
        assert len(result) == 2

    def test_as_of_date_excludes_all(self, fred_client, mock_urlopen):
        xml = make_observations_xml([
            {"date": "2024-06-01", "value": "100.0", "realtime_start": "2024-06-15"},
            {"date": "2024-07-01", "value": "101.0", "realtime_start": "2024-07-15"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series_as_of_date("TEST", "2024-01-01")
        assert len(result) == 0


# =========================================================================
# get_series_vintage_dates
# =========================================================================

class TestGetSeriesVintageDates:
    """Tests for Fred.get_series_vintage_dates."""

    def test_normal_dates(self, fred_client, mock_urlopen):
        dates = ["2024-01-30", "2024-02-28", "2024-03-27"]
        xml = make_vintage_dates_xml(dates)
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series_vintage_dates("GDP")
        assert len(result) == 3
        assert result[0] == datetime(2024, 1, 30)
        assert result[1] == datetime(2024, 2, 28)
        assert result[2] == datetime(2024, 3, 27)

    def test_empty_vintage_dates(self, fred_client, mock_urlopen):
        xml = make_vintage_dates_xml([])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series_vintage_dates("EMPTY")
        assert result == []

    def test_url_contains_series_id(self, fred_client, mock_urlopen):
        xml = make_vintage_dates_xml(["2024-01-01"])
        set_mock_response(mock_urlopen, xml)
        fred_client.get_series_vintage_dates("CPIAUCSL")
        called_url = mock_urlopen.call_args[0][0]
        assert "series_id=CPIAUCSL" in called_url
        assert "vintagedates" in called_url


# =========================================================================
# search
# =========================================================================

class TestSearch:
    """Tests for Fred.search."""

    def test_keyword_search_with_results(self, fred_client, mock_urlopen):
        xml = make_search_xml([
            {"id": "GDPPOT", "title": "Real Potential GDP"},
            {"id": "NGDPPOT", "title": "Nominal Potential GDP"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.search("potential gdp")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "GDPPOT" in result.index
        assert "NGDPPOT" in result.index

    def test_search_url_encoding(self, fred_client, mock_urlopen):
        xml = make_search_xml([{"id": "TEST", "title": "Test"}])
        set_mock_response(mock_urlopen, xml)
        fred_client.search("real gdp")
        called_url = mock_urlopen.call_args[0][0]
        assert "search_text=real+gdp" in called_url

    def test_empty_search_results(self, fred_client, mock_urlopen):
        xml = make_empty_search_xml()
        set_mock_response(mock_urlopen, xml)
        result = fred_client.search("xyznonexistent")
        assert result is None

    def test_order_by_parameter(self, fred_client, mock_urlopen):
        xml = make_search_xml([{"id": "A", "title": "A"}])
        set_mock_response(mock_urlopen, xml)
        fred_client.search("gdp", order_by="popularity")
        called_url = mock_urlopen.call_args[0][0]
        assert "order_by=popularity" in called_url

    def test_sort_order_parameter(self, fred_client, mock_urlopen):
        xml = make_search_xml([{"id": "A", "title": "A"}])
        set_mock_response(mock_urlopen, xml)
        fred_client.search("gdp", sort_order="desc")
        called_url = mock_urlopen.call_args[0][0]
        assert "sort_order=desc" in called_url

    def test_filter_parameter(self, fred_client, mock_urlopen):
        xml = make_search_xml([{"id": "A", "title": "A"}])
        set_mock_response(mock_urlopen, xml)
        fred_client.search("gdp", filter=("frequency", "Monthly"))
        called_url = mock_urlopen.call_args[0][0]
        assert "filter_variable=frequency" in called_url
        assert "filter_value=Monthly" in called_url

    def test_invalid_order_by_raises(self, fred_client, mock_urlopen):
        with pytest.raises(ValueError, match="not in the valid list of order_by"):
            fred_client.search("gdp", order_by="invalid_option")

    def test_invalid_sort_order_raises(self, fred_client, mock_urlopen):
        with pytest.raises(ValueError, match="not in the valid list of sort_order"):
            fred_client.search("gdp", sort_order="invalid")

    def test_invalid_filter_raises(self, fred_client, mock_urlopen):
        with pytest.raises(ValueError, match="Filter should be a 2 item tuple"):
            fred_client.search("gdp", filter=("only_one",))

    def test_pagination_multiple_requests(self, fred_client, mock_urlopen):
        """When total count > 1000, multiple HTTP requests are issued."""
        # First page: 1000 results, total count 1500
        page1_series = [{"id": f"S{i:04d}", "title": f"Series {i}"} for i in range(1000)]
        page1_xml = make_search_xml(page1_series, count=1500, offset=0, limit=1000)
        # Second page: 500 results
        page2_series = [{"id": f"S{i:04d}", "title": f"Series {i}"} for i in range(1000, 1500)]
        page2_xml = make_search_xml(page2_series, count=1500, offset=1000, limit=1000)

        mock_urlopen.return_value.read.side_effect = [page1_xml, page2_xml]
        result = fred_client.search("test", limit=1500)
        assert mock_urlopen.call_count == 2
        assert len(result) == 1500

    def test_search_limit_zero_fetches_all(self, fred_client, mock_urlopen):
        """limit=0 means fetch all results."""
        page1_series = [{"id": f"S{i:04d}", "title": f"Series {i}"} for i in range(1000)]
        page1_xml = make_search_xml(page1_series, count=1200, offset=0, limit=1000)
        page2_series = [{"id": f"S{i:04d}", "title": f"Series {i}"} for i in range(1000, 1200)]
        page2_xml = make_search_xml(page2_series, count=1200, offset=1000, limit=1000)

        mock_urlopen.return_value.read.side_effect = [page1_xml, page2_xml]
        result = fred_client.search("test", limit=0)
        assert mock_urlopen.call_count == 2
        assert len(result) == 1200

    def test_search_with_limit_less_than_total(self, fred_client, mock_urlopen):
        """When limit < total and limit <= 1000, only one request is needed."""
        series = [{"id": f"S{i:04d}", "title": f"Series {i}"} for i in range(5)]
        xml = make_search_xml(series, count=500)
        set_mock_response(mock_urlopen, xml)
        result = fred_client.search("test", limit=5)
        assert len(result) == 5
        assert mock_urlopen.call_count == 1

    def test_search_dataframe_columns(self, fred_client, mock_urlopen):
        xml = make_search_xml([{
            "id": "GDPPOT",
            "title": "Real Potential GDP",
            "frequency": "Quarterly",
            "frequency_short": "Q",
            "units": "Billions",
            "units_short": "Bil.",
            "seasonal_adjustment": "NSA",
            "seasonal_adjustment_short": "NSA",
            "popularity": "72",
        }])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.search("potential gdp")
        expected_cols = {"id", "title", "frequency", "frequency_short", "units",
                         "units_short", "seasonal_adjustment", "seasonal_adjustment_short",
                         "popularity", "realtime_start", "realtime_end",
                         "observation_start", "observation_end", "last_updated", "notes"}
        assert expected_cols.issubset(set(result.columns))
        assert result.index.name == "series id"


# =========================================================================
# search_by_release
# =========================================================================

class TestSearchByRelease:
    """Tests for Fred.search_by_release."""

    def test_normal_results(self, fred_client, mock_urlopen):
        xml = make_search_xml([
            {"id": "PCPI01001", "title": "Per Capita Personal Income Autauga"},
            {"id": "PCPI01003", "title": "Per Capita Personal Income Baldwin"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.search_by_release(175)
        assert len(result) == 2
        called_url = mock_urlopen.call_args[0][0]
        assert "release_id=175" in called_url

    def test_no_results_raises(self, fred_client, mock_urlopen):
        xml = make_empty_search_xml()
        set_mock_response(mock_urlopen, xml)
        with pytest.raises(ValueError, match="No series exists for release id"):
            fred_client.search_by_release(99999)

    def test_with_order_by(self, fred_client, mock_urlopen):
        xml = make_search_xml([{"id": "A", "title": "A"}])
        set_mock_response(mock_urlopen, xml)
        fred_client.search_by_release(175, order_by="series_id", sort_order="asc")
        called_url = mock_urlopen.call_args[0][0]
        assert "order_by=series_id" in called_url
        assert "sort_order=asc" in called_url


# =========================================================================
# search_by_category
# =========================================================================

class TestSearchByCategory:
    """Tests for Fred.search_by_category."""

    def test_normal_results(self, fred_client, mock_urlopen):
        xml = make_search_xml([
            {"id": "UNRATE", "title": "Unemployment Rate"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.search_by_category(32991)
        assert len(result) == 1
        called_url = mock_urlopen.call_args[0][0]
        assert "category_id=32991" in called_url

    def test_no_results_raises(self, fred_client, mock_urlopen):
        xml = make_empty_search_xml()
        set_mock_response(mock_urlopen, xml)
        with pytest.raises(ValueError, match="No series exists for category id"):
            fred_client.search_by_category(99999)

    def test_with_filter(self, fred_client, mock_urlopen):
        xml = make_search_xml([{"id": "A", "title": "A"}])
        set_mock_response(mock_urlopen, xml)
        fred_client.search_by_category(100, filter=("frequency", "Quarterly"))
        called_url = mock_urlopen.call_args[0][0]
        assert "filter_variable=frequency" in called_url
        assert "filter_value=Quarterly" in called_url


# =========================================================================
# Error handling / __fetch_data
# =========================================================================

class TestErrorHandling:
    """Tests for error handling in __fetch_data and related paths."""

    def test_http_error_extracts_message(self, fred_client, mock_urlopen):
        error_msg = "Bad Request. The series does not exist."
        error_xml = make_error_xml(400, error_msg)
        url = f"{Fred.root_url}/series/observations?series_id=BAD&api_key=test_api_key_12345"
        set_mock_http_error(mock_urlopen, url, 400, error_xml)
        with pytest.raises(ValueError, match="Bad Request"):
            fred_client.get_series("BAD")

    def test_http_500_error(self, fred_client, mock_urlopen):
        error_xml = make_error_xml(500, "Internal Server Error")
        url = f"{Fred.root_url}/series?series_id=ERR&api_key=test_api_key_12345"
        set_mock_http_error(mock_urlopen, url, 500, error_xml)
        with pytest.raises(ValueError, match="Internal Server Error"):
            fred_client.get_series_info("ERR")

    def test_url_error_propagates(self, fred_client, mock_urlopen):
        """When urlopen raises a non-HTTP error (e.g. URLError), it propagates."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        with pytest.raises(urllib.error.URLError):
            fred_client.get_series("TEST")

    def test_malformed_xml_raises(self, fred_client, mock_urlopen):
        """Completely malformed XML should raise an XML parsing error."""
        mock_urlopen.return_value.read.return_value = "this is not xml at all"
        with pytest.raises(Exception):
            fred_client.get_series("TEST")

    def test_api_key_appended_to_url(self, fred_client, mock_urlopen):
        xml = make_observations_xml([{"date": "2024-01-01", "value": "1.0"}])
        set_mock_response(mock_urlopen, xml)
        fred_client.get_series("TEST")
        called_url = mock_urlopen.call_args[0][0]
        assert "&api_key=test_api_key_12345" in called_url


# =========================================================================
# Parametrized tests
# =========================================================================

class TestParametrized:
    """Cross-cutting parametrized tests."""

    @pytest.mark.parametrize("series_id", ["GDP", "SP500", "CPIAUCSL", "UNRATE"])
    def test_get_series_various_ids(self, fred_client, mock_urlopen, series_id):
        xml = make_observations_xml([{"date": "2024-01-01", "value": "42.0"}])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.get_series(series_id)
        called_url = mock_urlopen.call_args[0][0]
        assert f"series_id={series_id}" in called_url
        assert len(result) == 1

    @pytest.mark.parametrize("order_by", [
        "search_rank", "series_id", "title", "units", "frequency",
        "seasonal_adjustment", "realtime_start", "realtime_end",
        "last_updated", "observation_start", "observation_end", "popularity",
    ])
    def test_search_valid_order_by_options(self, fred_client, mock_urlopen, order_by):
        xml = make_search_xml([{"id": "T", "title": "Test"}])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.search("test", order_by=order_by)
        called_url = mock_urlopen.call_args[0][0]
        assert f"order_by={order_by}" in called_url

    @pytest.mark.parametrize("sort_order", ["asc", "desc"])
    def test_search_valid_sort_orders(self, fred_client, mock_urlopen, sort_order):
        xml = make_search_xml([{"id": "T", "title": "Test"}])
        set_mock_response(mock_urlopen, xml)
        result = fred_client.search("test", sort_order=sort_order)
        called_url = mock_urlopen.call_args[0][0]
        assert f"sort_order={sort_order}" in called_url
