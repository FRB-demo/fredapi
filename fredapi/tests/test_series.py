"""Tests for Fred series retrieval methods."""

import math

import pandas as pd
import pytest

from fredapi.tests.conftest import (
    SAMPLE_ALL_RELEASES_OBSERVATIONS,
    SAMPLE_ALL_RELEASES_XML,
    SAMPLE_CPI_XML,
    SAMPLE_GDP_OBSERVATIONS,
    SAMPLE_GDP_XML,
    SAMPLE_PAYEMS_INFO,
    SAMPLE_PAYEMS_INFO_XML,
    SAMPLE_VINTAGE_DATES,
    SAMPLE_VINTAGE_DATES_XML,
    make_observations_xml,
    make_series_info_xml,
    set_mock_response,
)


class TestGetSeries:
    """Tests for Fred.get_series()."""

    def test_basic_series(self, fred, mock_urlopen):
        """get_series('GDP') returns pd.Series with DatetimeIndex and float values."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        result = fred.get_series("GDP")

        assert isinstance(result, pd.Series)
        assert isinstance(result.index, pd.DatetimeIndex)
        assert len(result) == len(SAMPLE_GDP_OBSERVATIONS)
        assert result.iloc[0] == 26138.0
        assert result.iloc[-1] == 27183.9

    def test_series_with_date_filtering(self, fred, mock_urlopen):
        """get_series with observation_start/end passes date params in URL."""
        set_mock_response(mock_urlopen, SAMPLE_CPI_XML)
        result = fred.get_series(
            "CPIAUCSL",
            observation_start="2020-01-01",
            observation_end="2023-12-31",
        )

        assert isinstance(result, pd.Series)
        assert len(result) == 6
        # Verify the URL contains the date parameters
        called_url = mock_urlopen.call_args[0][0]
        assert "observation_start=2020-01-01" in called_url
        assert "observation_end=2023-12-31" in called_url

    def test_series_with_kwargs(self, fred, mock_urlopen):
        """get_series passes additional kwargs as URL parameters."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        fred.get_series("GDP", units="chg", frequency="q")

        called_url = mock_urlopen.call_args[0][0]
        assert "units=chg" in called_url
        assert "frequency=q" in called_url

    def test_series_values_are_float(self, fred, mock_urlopen):
        """get_series values should all be float type."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        result = fred.get_series("GDP")

        for val in result.values:
            assert isinstance(val, float)

    def test_series_nan_values(self, fred, mock_urlopen):
        """get_series with value='.' should return NaN."""
        xml = make_observations_xml([
            {"date": "2023-01-01", "value": "100.0"},
            {"date": "2023-02-01", "value": "."},
            {"date": "2023-03-01", "value": "102.5"},
        ])
        set_mock_response(mock_urlopen, xml)
        result = fred.get_series("TEST")

        assert result.iloc[0] == 100.0
        assert math.isnan(result.iloc[1])
        assert result.iloc[2] == 102.5

    def test_series_api_key_in_url(self, fred, mock_urlopen):
        """get_series should append api_key to the URL."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        fred.get_series("GDP")

        called_url = mock_urlopen.call_args[0][0]
        assert "api_key=test_key" in called_url

    def test_series_correct_endpoint(self, fred, mock_urlopen):
        """get_series should call the series/observations endpoint."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        fred.get_series("GDP")

        called_url = mock_urlopen.call_args[0][0]
        assert "series/observations?series_id=GDP" in called_url


class TestGetSeriesInfo:
    """Tests for Fred.get_series_info()."""

    def test_basic_info(self, fred, mock_urlopen):
        """get_series_info returns pd.Series with metadata fields."""
        set_mock_response(mock_urlopen, SAMPLE_PAYEMS_INFO_XML)
        result = fred.get_series_info("PAYEMS")

        assert isinstance(result, pd.Series)
        assert result["id"] == "PAYEMS"
        assert result["title"] == "All Employees: Total Nonfarm Payrolls"
        assert result["frequency"] == "Monthly"
        assert result["frequency_short"] == "M"
        assert result["units"] == "Thousands of Persons"
        assert result["seasonal_adjustment"] == "Seasonally Adjusted"

    def test_info_all_fields_present(self, fred, mock_urlopen):
        """get_series_info should contain all expected metadata fields."""
        set_mock_response(mock_urlopen, SAMPLE_PAYEMS_INFO_XML)
        result = fred.get_series_info("PAYEMS")

        for key in SAMPLE_PAYEMS_INFO:
            assert key in result.index, f"Missing field: {key}"

    def test_info_correct_endpoint(self, fred, mock_urlopen):
        """get_series_info should call the series endpoint."""
        set_mock_response(mock_urlopen, SAMPLE_PAYEMS_INFO_XML)
        fred.get_series_info("PAYEMS")

        called_url = mock_urlopen.call_args[0][0]
        assert "series?series_id=PAYEMS" in called_url


class TestGetSeriesLatestRelease:
    """Tests for Fred.get_series_latest_release()."""

    def test_delegates_to_get_series(self, fred, mock_urlopen):
        """get_series_latest_release should delegate to get_series."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        result = fred.get_series_latest_release("GDP")

        assert isinstance(result, pd.Series)
        assert len(result) == len(SAMPLE_GDP_OBSERVATIONS)
        called_url = mock_urlopen.call_args[0][0]
        assert "series/observations?series_id=GDP" in called_url


class TestGetSeriesFirstRelease:
    """Tests for Fred.get_series_first_release()."""

    def test_first_release_returns_first_values(self, fred, mock_urlopen):
        """get_series_first_release returns only first release for each date."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_first_release("GDP")

        assert isinstance(result, pd.Series)
        # 2023-10-01 appears 3 times in all_releases; first_release keeps only the first
        dates_2023_q4 = [d for d in result.index if d.year == 2023 and d.month == 10]
        assert len(dates_2023_q4) == 1
        # The first release value for 2023-10-01 is 27183.9
        assert result.iloc[0] == 27183.9

    def test_first_release_preserves_all_unique_dates(self, fred, mock_urlopen):
        """get_series_first_release returns one value per observation date."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_first_release("GDP")

        # We have 2 unique dates: 2023-10-01 (3 releases) and 2024-01-01 (1 release)
        assert len(result) == 2


class TestGetSeriesAsOfDate:
    """Tests for Fred.get_series_as_of_date()."""

    def test_as_of_date_filters_by_realtime(self, fred, mock_urlopen):
        """get_series_as_of_date filters by realtime_start <= as_of_date."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_as_of_date("GDP", "2024-02-28")

        # Should include observations with realtime_start <= 2024-02-28
        # That's 2024-01-30 and 2024-02-28 (both for date 2023-10-01)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_as_of_date_includes_boundary(self, fred, mock_urlopen):
        """as_of_date on exact realtime_start should include that observation."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_as_of_date("GDP", "2024-01-30")

        assert len(result) == 1


class TestGetSeriesAllReleases:
    """Tests for Fred.get_series_all_releases()."""

    def test_returns_dataframe(self, fred, mock_urlopen):
        """get_series_all_releases returns a DataFrame."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_all_releases("GDP")

        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self, fred, mock_urlopen):
        """get_series_all_releases DataFrame has date, realtime_start, value columns."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_all_releases("GDP")

        assert "date" in result.columns
        assert "realtime_start" in result.columns
        assert "value" in result.columns

    def test_correct_row_count(self, fred, mock_urlopen):
        """get_series_all_releases returns one row per observation element."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_all_releases("GDP")

        assert len(result) == len(SAMPLE_ALL_RELEASES_OBSERVATIONS)

    def test_values_match(self, fred, mock_urlopen):
        """get_series_all_releases values match the XML data."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_all_releases("GDP")

        assert result.iloc[0]["value"] == 27183.9
        assert result.iloc[1]["value"] == 27200.1

    def test_uses_earliest_realtime_start_default(self, fred, mock_urlopen):
        """get_series_all_releases uses earliest_realtime_start by default."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        fred.get_series_all_releases("GDP")

        called_url = mock_urlopen.call_args[0][0]
        assert "realtime_start=1776-07-04" in called_url
        assert "realtime_end=9999-12-31" in called_url

    def test_custom_realtime_range(self, fred, mock_urlopen):
        """get_series_all_releases passes custom realtime_start/end."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        fred.get_series_all_releases("GDP", realtime_start="2024-01-01", realtime_end="2024-06-01")

        called_url = mock_urlopen.call_args[0][0]
        assert "realtime_start=2024-01-01" in called_url
        assert "realtime_end=2024-06-01" in called_url


class TestGetSeriesVintageDates:
    """Tests for Fred.get_series_vintage_dates()."""

    def test_returns_list_of_datetimes(self, fred, mock_urlopen):
        """get_series_vintage_dates returns a list of datetime objects."""
        set_mock_response(mock_urlopen, SAMPLE_VINTAGE_DATES_XML)
        result = fred.get_series_vintage_dates("GDP")

        assert isinstance(result, list)
        assert len(result) == len(SAMPLE_VINTAGE_DATES)
        for item in result:
            assert hasattr(item, "year")  # datetime-like

    def test_vintage_dates_values(self, fred, mock_urlopen):
        """get_series_vintage_dates returns correct date values."""
        set_mock_response(mock_urlopen, SAMPLE_VINTAGE_DATES_XML)
        result = fred.get_series_vintage_dates("GDP")

        assert result[0].year == 2024
        assert result[0].month == 1
        assert result[0].day == 30

    def test_vintage_dates_endpoint(self, fred, mock_urlopen):
        """get_series_vintage_dates calls the correct endpoint."""
        set_mock_response(mock_urlopen, SAMPLE_VINTAGE_DATES_XML)
        fred.get_series_vintage_dates("GDP")

        called_url = mock_urlopen.call_args[0][0]
        assert "series/vintagedates?series_id=GDP" in called_url
