"""Tests for Fred search methods."""

import pytest

import pandas as pd

from fredapi.tests.conftest import (
    SAMPLE_EMPTY_SEARCH_XML,
    SAMPLE_SEARCH_SERIES,
    SAMPLE_SEARCH_XML,
    make_search_xml,
    set_mock_response,
)


class TestSearch:
    """Tests for Fred.search()."""

    def test_basic_search(self, fred, mock_urlopen):
        """search('Real GDP') returns DataFrame with expected columns."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        result = fred.search("Real GDP")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(SAMPLE_SEARCH_SERIES)

    def test_search_has_expected_columns(self, fred, mock_urlopen):
        """search result DataFrame contains standard metadata columns."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        result = fred.search("Real GDP")

        expected_columns = [
            "id", "title", "observation_start", "observation_end",
            "frequency", "units", "popularity",
        ]
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"

    def test_search_values(self, fred, mock_urlopen):
        """search returns correct series data."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        result = fred.search("Real GDP")

        assert "GDPC1" in result.index
        assert result.loc["GDPC1", "title"] == "Real Gross Domestic Product"

    def test_search_with_limit(self, fred, mock_urlopen):
        """search with limit parameter limits results."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        result = fred.search("Real GDP", limit=2)

        assert len(result) <= 2

    def test_search_with_order_by(self, fred, mock_urlopen):
        """search with order_by passes parameter in URL."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        fred.search("Real GDP", order_by="popularity")

        called_url = mock_urlopen.call_args[0][0]
        assert "order_by=popularity" in called_url

    def test_search_with_sort_order(self, fred, mock_urlopen):
        """search with sort_order passes parameter in URL."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        fred.search("Real GDP", sort_order="desc")

        called_url = mock_urlopen.call_args[0][0]
        assert "sort_order=desc" in called_url

    def test_search_with_filter(self, fred, mock_urlopen):
        """search with filter tuple passes filter params in URL."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        fred.search("Real GDP", filter=("frequency", "Quarterly"))

        called_url = mock_urlopen.call_args[0][0]
        assert "filter_variable=frequency" in called_url
        assert "filter_value=Quarterly" in called_url

    def test_search_invalid_order_by_raises(self, fred, mock_urlopen):
        """search with invalid order_by raises ValueError."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        with pytest.raises(ValueError):
            fred.search("Real GDP", order_by="invalid_field")

    def test_search_invalid_sort_order_raises(self, fred, mock_urlopen):
        """search with invalid sort_order raises ValueError."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        with pytest.raises(ValueError):
            fred.search("Real GDP", sort_order="invalid")

    def test_search_invalid_filter_raises(self, fred, mock_urlopen):
        """search with wrongly-sized filter raises ValueError."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        with pytest.raises(ValueError):
            fred.search("Real GDP", filter=("only_one_element",))

    def test_search_url_encodes_text(self, fred, mock_urlopen):
        """search URL-encodes the search text."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        fred.search("Real GDP")

        called_url = mock_urlopen.call_args[0][0]
        assert "search_text=Real+GDP" in called_url

    def test_search_index_name(self, fred, mock_urlopen):
        """search DataFrame index name should be 'series id'."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        result = fred.search("Real GDP")

        assert result.index.name == "series id"

    def test_search_pagination_multiple_requests(self, fred, mock_urlopen):
        """search with >1000 results triggers multiple HTTP requests."""
        # First call returns page 1 with count=1500 (indicating more data)
        page1_series = [
            {"id": f"SER{i:04d}", "title": f"Series {i}"}
            for i in range(1000)
        ]
        page1_xml = make_search_xml(page1_series, count=1500, offset=0, limit=1000)

        # Second call returns page 2
        page2_series = [
            {"id": f"SER{i:04d}", "title": f"Series {i}"}
            for i in range(1000, 1500)
        ]
        page2_xml = make_search_xml(page2_series, count=1500, offset=1000, limit=1000)

        mock_urlopen.return_value.read.side_effect = [page1_xml, page2_xml]
        result = fred.search("test", limit=0)

        # Should have made 2 HTTP calls
        assert mock_urlopen.call_count == 2
        # Second call should have offset=1000
        second_url = mock_urlopen.call_args_list[1][0][0]
        assert "offset=1000" in second_url


class TestSearchByRelease:
    """Tests for Fred.search_by_release()."""

    def test_basic_search_by_release(self, fred, mock_urlopen):
        """search_by_release returns DataFrame."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        result = fred.search_by_release(175)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(SAMPLE_SEARCH_SERIES)

    def test_search_by_release_url(self, fred, mock_urlopen):
        """search_by_release uses correct URL with release_id."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        fred.search_by_release(175)

        called_url = mock_urlopen.call_args[0][0]
        assert "release/series?release_id=175" in called_url

    def test_search_by_release_nonexistent_raises(self, fred, mock_urlopen):
        """search_by_release with non-existent release raises ValueError."""
        set_mock_response(mock_urlopen, SAMPLE_EMPTY_SEARCH_XML)
        with pytest.raises(ValueError, match="No series exists for release id"):
            fred.search_by_release(999999)

    def test_search_by_release_with_order_by(self, fred, mock_urlopen):
        """search_by_release passes order_by parameter."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        fred.search_by_release(175, order_by="series_id", sort_order="asc")

        called_url = mock_urlopen.call_args[0][0]
        assert "order_by=series_id" in called_url
        assert "sort_order=asc" in called_url


class TestSearchByCategory:
    """Tests for Fred.search_by_category()."""

    def test_basic_search_by_category(self, fred, mock_urlopen):
        """search_by_category returns DataFrame."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        result = fred.search_by_category(32145)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(SAMPLE_SEARCH_SERIES)

    def test_search_by_category_url(self, fred, mock_urlopen):
        """search_by_category uses correct URL with category_id."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        fred.search_by_category(32145)

        called_url = mock_urlopen.call_args[0][0]
        assert "category/series?category_id=32145" in called_url

    def test_search_by_category_nonexistent_raises(self, fred, mock_urlopen):
        """search_by_category with non-existent category raises ValueError."""
        set_mock_response(mock_urlopen, SAMPLE_EMPTY_SEARCH_XML)
        with pytest.raises(ValueError, match="No series exists for category id"):
            fred.search_by_category(999999)

    def test_search_by_category_with_filter(self, fred, mock_urlopen):
        """search_by_category passes filter parameter."""
        set_mock_response(mock_urlopen, SAMPLE_SEARCH_XML)
        fred.search_by_category(32145, filter=("frequency", "Monthly"))

        called_url = mock_urlopen.call_args[0][0]
        assert "filter_variable=frequency" in called_url
        assert "filter_value=Monthly" in called_url
