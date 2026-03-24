"""Regression tests to verify return types and data contracts."""

import pandas as pd
import pytest

from fredapi.tests.conftest import (
    SAMPLE_ALL_RELEASES_XML,
    SAMPLE_GDP_XML,
    SAMPLE_PAYEMS_INFO_XML,
    SAMPLE_SEARCH_XML,
    set_mock_response,
)


class TestGetSeriesReturnType:
    """Verify get_series return type contracts."""

    def test_returns_series_not_dataframe(self, fred, mock_urlopen):
        """get_series must return pd.Series (not DataFrame)."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        result = fred.get_series("GDP")

        assert isinstance(result, pd.Series)
        assert not isinstance(result, pd.DataFrame)

    def test_index_is_datetimeindex(self, fred, mock_urlopen):
        """get_series index must be DatetimeIndex."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        result = fred.get_series("GDP")

        assert isinstance(result.index, pd.DatetimeIndex)

    def test_values_are_float(self, fred, mock_urlopen):
        """get_series values must be float type."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        result = fred.get_series("GDP")

        for val in result.values:
            assert isinstance(val, float), f"Expected float, got {type(val)}"

    def test_index_dates_match_observations(self, fred, mock_urlopen):
        """get_series index dates should correspond to observation dates."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        result = fred.get_series("GDP")

        # The GDP sample has 4 quarterly observations in 2023
        assert result.index[0] == pd.Timestamp("2023-01-01")
        assert result.index[-1] == pd.Timestamp("2023-10-01")


class TestSearchReturnType:
    """Verify search return type contracts."""

    def test_returns_dataframe(self, fred, mock_urlopen):
        """search must return pd.DataFrame."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        result = fred.search("Real GDP")

        assert isinstance(result, pd.DataFrame)

    def test_has_expected_columns(self, fred, mock_urlopen):
        """search DataFrame must have standard metadata columns."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        result = fred.search("Real GDP")

        required_columns = [
            "id", "title", "observation_start", "observation_end",
            "frequency", "units", "seasonal_adjustment", "popularity",
        ]
        for col in required_columns:
            assert col in result.columns, f"Missing required column: {col}"

    def test_index_is_series_id(self, fred, mock_urlopen):
        """search DataFrame index should be series ids."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        result = fred.search("Real GDP")

        assert result.index.name == "series id"
        assert "GDPC1" in result.index

    def test_datetime_columns_parsed(self, fred, mock_urlopen):
        """search should parse datetime columns."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        result = fred.search("Real GDP")

        # observation_start should be parsed to datetime
        obs_start = result.loc["GDPC1", "observation_start"]
        assert hasattr(obs_start, "year")


class TestGetSeriesAllReleasesReturnType:
    """Verify get_series_all_releases return type contracts."""

    def test_returns_dataframe(self, fred, mock_urlopen):
        """get_series_all_releases must return pd.DataFrame."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_all_releases("GDP")

        assert isinstance(result, pd.DataFrame)

    def test_has_exactly_three_columns(self, fred, mock_urlopen):
        """get_series_all_releases DataFrame must have exactly 3 columns."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_all_releases("GDP")

        assert set(result.columns) == {"date", "realtime_start", "value"}

    def test_date_column_is_datetime(self, fred, mock_urlopen):
        """get_series_all_releases 'date' column should contain datetime objects."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_all_releases("GDP")

        for dt in result["date"]:
            assert hasattr(dt, "year"), f"Expected datetime, got {type(dt)}"

    def test_realtime_start_column_is_datetime(self, fred, mock_urlopen):
        """get_series_all_releases 'realtime_start' column should contain datetime objects."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_all_releases("GDP")

        for dt in result["realtime_start"]:
            assert hasattr(dt, "year"), f"Expected datetime, got {type(dt)}"

    def test_value_column_is_float(self, fred, mock_urlopen):
        """get_series_all_releases 'value' column should contain floats."""
        set_mock_response(mock_urlopen, SAMPLE_ALL_RELEASES_XML)
        result = fred.get_series_all_releases("GDP")

        for val in result["value"]:
            assert isinstance(val, float), f"Expected float, got {type(val)}"


class TestGetSeriesInfoReturnType:
    """Verify get_series_info return type contracts."""

    def test_returns_series(self, fred, mock_urlopen):
        """get_series_info must return pd.Series."""
        set_mock_response(mock_urlopen, SAMPLE_PAYEMS_INFO_XML)
        result = fred.get_series_info("PAYEMS")

        assert isinstance(result, pd.Series)
        assert not isinstance(result, pd.DataFrame)


class TestDateFilteringBehavior:
    """Verify that date filtering actually works."""

    def test_observation_start_included_in_url(self, fred, mock_urlopen):
        """observation_start should be included in the request URL."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        fred.get_series("GDP", observation_start="2023-01-01")

        called_url = mock_urlopen.call_args[0][0]
        assert "observation_start=2023-01-01" in called_url

    def test_observation_end_included_in_url(self, fred, mock_urlopen):
        """observation_end should be included in the request URL."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        fred.get_series("GDP", observation_end="2023-12-31")

        called_url = mock_urlopen.call_args[0][0]
        assert "observation_end=2023-12-31" in called_url

    def test_both_dates_included_in_url(self, fred, mock_urlopen):
        """Both observation_start and observation_end should be in URL."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        fred.get_series(
            "GDP",
            observation_start="2023-01-01",
            observation_end="2023-12-31",
        )

        called_url = mock_urlopen.call_args[0][0]
        assert "observation_start=2023-01-01" in called_url
        assert "observation_end=2023-12-31" in called_url

    def test_date_format_conversion(self, fred, mock_urlopen):
        """Various date formats should be converted to YYYY-MM-DD."""
        set_mock_response(mock_urlopen, SAMPLE_GDP_XML)
        fred.get_series("GDP", observation_start="1/15/2023")

        called_url = mock_urlopen.call_args[0][0]
        assert "observation_start=2023-01-15" in called_url
