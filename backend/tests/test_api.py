import os
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient


class TestSearchEndpoint:
    """Tests for GET /api/search."""

    def test_search_returns_results(self, client, mock_fred, sample_search_results):
        mock_fred.search.return_value = sample_search_results
        response = client.get("/api/search", params={"q": "potential gdp"})
        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 2
        assert len(body["results"]) == 2
        assert body["results"][0]["id"] == "GDPPOT"
        assert body["results"][1]["id"] == "NGDPPOT"
        mock_fred.search.assert_called_once_with(
            "potential gdp", limit=1000, order_by=None, sort_order=None
        )

    def test_search_empty_query(self, client, mock_fred):
        response = client.get("/api/search", params={"q": ""})
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_search_no_results(self, client, mock_fred):
        mock_fred.search.return_value = None
        response = client.get("/api/search", params={"q": "xyznonexistent"})
        assert response.status_code == 200
        body = response.json()
        assert body["results"] == []
        assert body["count"] == 0

    def test_search_with_params(self, client, mock_fred, sample_search_results):
        mock_fred.search.return_value = sample_search_results
        response = client.get(
            "/api/search",
            params={
                "q": "gdp",
                "limit": 10,
                "order_by": "popularity",
                "sort_order": "desc",
            },
        )
        assert response.status_code == 200
        mock_fred.search.assert_called_once_with(
            "gdp", limit=10, order_by="popularity", sort_order="desc"
        )


class TestGetSeriesEndpoint:
    """Tests for GET /api/series/{series_id}."""

    def test_get_series(self, client, mock_fred, sample_series):
        mock_fred.get_series.return_value = sample_series
        response = client.get("/api/series/GDP")
        assert response.status_code == 200
        body = response.json()
        assert body["series_id"] == "GDP"
        assert len(body["observations"]) == 3
        assert body["observations"][0]["date"] == "2024-01-01"
        assert body["observations"][0]["value"] == 100.0
        mock_fred.get_series.assert_called_once_with(
            "GDP", observation_start=None, observation_end=None
        )

    def test_get_series_with_date_range(self, client, mock_fred, sample_series):
        mock_fred.get_series.return_value = sample_series
        response = client.get(
            "/api/series/SP500",
            params={
                "observation_start": "2024-01-01",
                "observation_end": "2024-03-01",
            },
        )
        assert response.status_code == 200
        mock_fred.get_series.assert_called_once_with(
            "SP500",
            observation_start="2024-01-01",
            observation_end="2024-03-01",
        )

    def test_get_series_not_found(self, client, mock_fred):
        mock_fred.get_series.side_effect = ValueError(
            "No data exists for series id: INVALID"
        )
        response = client.get("/api/series/INVALID")
        assert response.status_code == 404
        assert "INVALID" in response.json()["detail"]

    def test_nan_handling(self, client, mock_fred, sample_series):
        mock_fred.get_series.return_value = sample_series
        response = client.get("/api/series/TEST")
        assert response.status_code == 200
        body = response.json()
        # Third observation has NaN which should be serialized as null/None
        assert body["observations"][2]["value"] is None


class TestGetSeriesInfoEndpoint:
    """Tests for GET /api/series/{series_id}/info."""

    def test_get_series_info(self, client, mock_fred, sample_info):
        mock_fred.get_series_info.return_value = sample_info
        response = client.get("/api/series/GDP/info")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == "GDP"
        assert body["title"] == "Gross Domestic Product"
        assert body["frequency"] == "Quarterly"
        assert body["units"] == "Billions of Dollars"

    def test_get_series_info_not_found(self, client, mock_fred):
        mock_fred.get_series_info.side_effect = ValueError(
            "No info exists for series id: INVALID"
        )
        response = client.get("/api/series/INVALID/info")
        assert response.status_code == 404


class TestGetSeriesReleasesEndpoint:
    """Tests for GET /api/series/{series_id}/releases."""

    def test_get_series_releases(self, client, mock_fred, sample_releases):
        mock_fred.get_series_all_releases.return_value = sample_releases
        response = client.get("/api/series/GDP/releases")
        assert response.status_code == 200
        body = response.json()
        assert body["series_id"] == "GDP"
        assert len(body["releases"]) == 3
        assert body["releases"][0]["date"] == "2024-01-01"
        assert body["releases"][0]["value"] == 17149.6


class TestGetVintageDatesEndpoint:
    """Tests for GET /api/series/{series_id}/vintage-dates."""

    def test_get_vintage_dates(self, client, mock_fred, sample_vintage_dates):
        mock_fred.get_series_vintage_dates.return_value = sample_vintage_dates
        response = client.get("/api/series/GDP/vintage-dates")
        assert response.status_code == 200
        body = response.json()
        assert body["series_id"] == "GDP"
        assert len(body["vintage_dates"]) == 4
        assert body["vintage_dates"][0] == "2024-01-30"
        assert body["vintage_dates"][3] == "2024-04-30"


class TestGetSeriesAsOfEndpoint:
    """Tests for GET /api/series/{series_id}/as-of."""

    def test_get_series_as_of(self, client, mock_fred, sample_as_of_data):
        mock_fred.get_series_as_of_date.return_value = sample_as_of_data
        response = client.get(
            "/api/series/GDP/as-of", params={"date": "2024-06-01"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["series_id"] == "GDP"
        assert body["as_of_date"] == "2024-06-01"
        assert len(body["data"]) == 2

    def test_get_series_as_of_not_found(self, client, mock_fred):
        mock_fred.get_series_as_of_date.side_effect = ValueError(
            "No data exists for series id: INVALID"
        )
        response = client.get(
            "/api/series/INVALID/as-of", params={"date": "2024-01-01"}
        )
        assert response.status_code == 404


class TestMissingApiKey:
    """Test behavior when FRED_API_KEY is not set."""

    def test_missing_api_key(self):
        # Remove the env var and create a fresh client
        env = os.environ.copy()
        env.pop("FRED_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            from backend.app import app

            test_client = TestClient(app)
            response = test_client.get("/api/search", params={"q": "gdp"})
            assert response.status_code == 500
            assert "FRED_API_KEY" in response.json()["detail"]
