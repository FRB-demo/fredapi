import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    """Set a fake FRED_API_KEY for all tests."""
    monkeypatch.setenv("FRED_API_KEY", "test_api_key_123")


@pytest.fixture()
def mock_fred():
    """Return a MagicMock that replaces the Fred constructor."""
    with patch("backend.app.Fred") as MockFred:
        instance = MagicMock()
        MockFred.return_value = instance
        yield instance


@pytest.fixture()
def client(mock_fred):
    """Create a FastAPI TestClient with a mocked Fred instance."""
    from backend.app import app

    return TestClient(app)


@pytest.fixture()
def sample_series():
    """Return a sample pandas Series mimicking Fred.get_series() output."""
    index = pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"])
    return pd.Series([100.0, 101.5, float("nan")], index=index)


@pytest.fixture()
def sample_info():
    """Return a sample pandas Series mimicking Fred.get_series_info() output."""
    return pd.Series(
        {
            "id": "GDP",
            "title": "Gross Domestic Product",
            "observation_start": "1947-01-01",
            "observation_end": "2024-01-01",
            "frequency": "Quarterly",
            "frequency_short": "Q",
            "units": "Billions of Dollars",
            "units_short": "Bil. of $",
            "seasonal_adjustment": "Seasonally Adjusted",
            "seasonal_adjustment_short": "SA",
            "last_updated": "2024-03-28 07:46:02-05",
            "popularity": "93",
            "notes": "GDP measures the value of goods and services produced.",
        }
    )


@pytest.fixture()
def sample_releases():
    """Return a sample DataFrame mimicking Fred.get_series_all_releases() output."""
    return pd.DataFrame(
        {
            "date": [datetime(2024, 1, 1), datetime(2024, 1, 1), datetime(2024, 4, 1)],
            "realtime_start": [
                datetime(2024, 4, 25),
                datetime(2024, 5, 30),
                datetime(2024, 7, 25),
            ],
            "value": [17149.6, 17101.3, 17294.7],
        }
    )


@pytest.fixture()
def sample_search_results():
    """Return a sample DataFrame mimicking Fred.search() output."""
    data = {
        "GDPPOT": {
            "id": "GDPPOT",
            "title": "Real Potential Gross Domestic Product",
            "frequency": "Quarterly",
            "units": "Billions of Chained 2009 Dollars",
            "seasonal_adjustment": "Not Seasonally Adjusted",
            "popularity": "72",
            "last_updated": "2024-02-04 10:06:03-06",
            "observation_start": "1949-01-01",
            "observation_end": "2024-10-01",
        },
        "NGDPPOT": {
            "id": "NGDPPOT",
            "title": "Nominal Potential Gross Domestic Product",
            "frequency": "Quarterly",
            "units": "Billions of Dollars",
            "seasonal_adjustment": "Not Seasonally Adjusted",
            "popularity": "61",
            "last_updated": "2024-02-04 10:06:03-06",
            "observation_start": "1949-01-01",
            "observation_end": "2024-10-01",
        },
    }
    df = pd.DataFrame(data).T
    df.index.name = "series id"
    return df


@pytest.fixture()
def sample_vintage_dates():
    """Return a sample list mimicking Fred.get_series_vintage_dates() output."""
    return [
        datetime(2024, 1, 30),
        datetime(2024, 2, 28),
        datetime(2024, 3, 27),
        datetime(2024, 4, 30),
    ]


@pytest.fixture()
def sample_as_of_data():
    """Return a sample DataFrame mimicking Fred.get_series_as_of_date() output."""
    return pd.DataFrame(
        {
            "date": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
            "realtime_start": [datetime(2024, 4, 25), datetime(2024, 5, 30)],
            "value": [17149.6, 17101.3],
        }
    )
