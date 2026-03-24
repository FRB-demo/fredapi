"""Shared pytest fixtures and XML response factories for fredapi tests."""

import io
from datetime import datetime
from unittest import mock

import pytest

import fredapi
import fredapi.fred


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fred_client():
    """Return a Fred instance initialised with a deterministic test API key."""
    return fredapi.Fred(api_key="test_api_key_12345")


@pytest.fixture
def mock_urlopen():
    """Patch ``fredapi.fred.urlopen`` for the duration of a test.

    Yields the mock so tests can configure ``return_value.read.return_value``.
    """
    with mock.patch("fredapi.fred.urlopen") as m:
        yield m


# ---------------------------------------------------------------------------
# XML response factory helpers
# ---------------------------------------------------------------------------

def make_observations_xml(observations, extra_attrs=None):
    """Build a FRED observations XML response."""
    attrs = {
        "realtime_start": "2024-01-01",
        "realtime_end": "2024-01-01",
        "observation_start": "1776-07-04",
        "observation_end": "9999-12-31",
        "units": "lin",
        "output_type": "1",
        "file_type": "xml",
        "order_by": "observation_date",
        "sort_order": "asc",
        "count": str(len(observations)),
        "offset": "0",
        "limit": "100000",
    }
    if extra_attrs:
        attrs.update(extra_attrs)
    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    obs_lines = []
    for obs in observations:
        rt_start = obs.get("realtime_start", "2024-01-01")
        rt_end = obs.get("realtime_end", "2024-01-01")
        obs_lines.append(
            f'<observation realtime_start="{rt_start}" realtime_end="{rt_end}" '
            f'date="{obs["date"]}" value="{obs["value"]}"/>'
        )
    children = "\n".join(obs_lines)
    lines = [
        '<?xml version="1.0" encoding="utf-8" ?>',
        f'<observations {attr_str}>',
        children,
        '</observations>',
    ]
    return "\n".join(lines)


def make_series_info_xml(attrs):
    """Build a FRED series info XML response."""
    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    lines = [
        '<?xml version="1.0" encoding="utf-8" ?>',
        '<seriess realtime_start="2024-01-01" realtime_end="2024-01-01">',
        f'  <series {attr_str} />',
        '</seriess>',
    ]
    return "\n".join(lines)


def make_empty_series_info_xml():
    """Build a FRED series info XML with no <series> children."""
    lines = [
        '<?xml version="1.0" encoding="utf-8" ?>',
        '<seriess realtime_start="2024-01-01" realtime_end="2024-01-01">',
        '</seriess>',
    ]
    return "\n".join(lines)


def make_search_xml(series_list, count=None, offset=0, limit=1000):
    """Build a FRED series search XML response."""
    if count is None:
        count = len(series_list)
    defaults = {
        "realtime_start": "2024-01-01",
        "realtime_end": "2024-01-01",
        "observation_start": "2000-01-01",
        "observation_end": "2024-01-01",
        "frequency": "Monthly",
        "frequency_short": "M",
        "units": "Index",
        "units_short": "Index",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "seasonal_adjustment_short": "NSA",
        "last_updated": "2024-01-01 08:00:00-06",
        "popularity": "50",
        "notes": "Test notes",
    }
    series_elements = []
    for s in series_list:
        merged = {**defaults, **s}
        attr_str = " ".join(f'{k}="{v}"' for k, v in merged.items())
        series_elements.append(f"  <series {attr_str} />")
    children = "\n".join(series_elements)
    lines = [
        '<?xml version="1.0" encoding="utf-8" ?>',
        '<seriess realtime_start="2024-01-01" realtime_end="2024-01-01"'
        f' order_by="series_id" sort_order="asc" count="{count}"'
        f' offset="{offset}" limit="{limit}">',
        children,
        '</seriess>',
    ]
    return "\n".join(lines)


def make_empty_search_xml():
    """Build a FRED search XML with zero results."""
    lines = [
        '<?xml version="1.0" encoding="utf-8" ?>',
        '<seriess realtime_start="2024-01-01" realtime_end="2024-01-01"'
        ' order_by="series_id" sort_order="asc" count="0"'
        ' offset="0" limit="1000">',
        '</seriess>',
    ]
    return "\n".join(lines)


def make_vintage_dates_xml(dates):
    """Build a FRED vintage dates XML response."""
    elements = "\n".join(f"  <vintage_date>{d}</vintage_date>" for d in dates)
    lines = [
        '<?xml version="1.0" encoding="utf-8" ?>',
        '<vintage_dates realtime_start="1776-07-04" realtime_end="9999-12-31"'
        ' order_by="vintage_date" sort_order="asc"'
        f' count="{len(dates)}">',
        elements,
        '</vintage_dates>',
    ]
    return "\n".join(lines)


def make_error_xml(code, message):
    """Build a FRED error XML response."""
    lines = [
        '<?xml version="1.0" encoding="utf-8" ?>',
        f'<error code="{code}" message="{message}" />',
    ]
    return "\n".join(lines)


def set_mock_response(mock_urlopen, xml_string):
    """Configure *mock_urlopen* to return *xml_string* on read()."""
    mock_urlopen.return_value.read.return_value = xml_string


def set_mock_http_error(mock_urlopen, url, code, xml_string):
    """Configure *mock_urlopen* to raise an HTTPError whose body is *xml_string*."""
    fp = io.StringIO(xml_string)
    mock_urlopen.side_effect = fredapi.fred.HTTPError(url, code, "Error", {}, fp)
