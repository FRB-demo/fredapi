"""Shared pytest fixtures and helpers for fredapi tests."""

import textwrap
from unittest.mock import patch

import pytest

from fredapi import Fred


# ---------------------------------------------------------------------------
# XML response helpers
# ---------------------------------------------------------------------------

def make_observations_xml(observations, extra_attrs=""):
    """Generate a FRED observations XML response.

    Parameters
    ----------
    observations : list[dict]
        Each dict should have 'date' and 'value' keys.  Optionally
        'realtime_start' and 'realtime_end'.
    extra_attrs : str
        Extra attributes to include on the root <observations> element.

    Returns
    -------
    str
    """
    obs_lines = []
    for obs in observations:
        rt_start = obs.get("realtime_start", "2024-01-01")
        rt_end = obs.get("realtime_end", "2024-01-01")
        date = obs["date"]
        value = obs["value"]
        obs_lines.append(
            f'  <observation realtime_start="{rt_start}" realtime_end="{rt_end}" '
            f'date="{date}" value="{value}"/>'
        )
    obs_block = "\n".join(obs_lines)
    return textwrap.dedent(f"""\
<?xml version="1.0" encoding="utf-8" ?>
<observations count="{len(observations)}" offset="0" limit="100000" {extra_attrs}>
{obs_block}
</observations>""")


def make_series_info_xml(attrs):
    """Generate a FRED series info XML response.

    Parameters
    ----------
    attrs : dict
        Key/value pairs that become attributes on the <series> element.

    Returns
    -------
    str
    """
    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return textwrap.dedent(f"""\
<?xml version="1.0" encoding="utf-8" ?>
<seriess realtime_start="2024-01-01" realtime_end="2024-01-01">
  <series {attr_str} />
</seriess>""")


def make_vintage_dates_xml(dates):
    """Generate a FRED vintage dates XML response.

    Parameters
    ----------
    dates : list[str]
        Date strings like '2024-01-30'.

    Returns
    -------
    str
    """
    date_lines = "\n".join(f"  <vintage_date>{d}</vintage_date>" for d in dates)
    return textwrap.dedent(f"""\
<?xml version="1.0" encoding="utf-8" ?>
<vintage_dates count="{len(dates)}">
{date_lines}
</vintage_dates>""")


def make_search_xml(series_list, count=None, offset=0, limit=1000):
    """Generate a FRED series search XML response.

    Parameters
    ----------
    series_list : list[dict]
        Each dict should have at minimum 'id' and 'title'.
    count : int or None
        Total count attribute. Defaults to len(series_list).
    offset : int
        Offset attribute.
    limit : int
        Limit attribute.

    Returns
    -------
    str
    """
    if count is None:
        count = len(series_list)
    lines = []
    for s in series_list:
        attrs = {
            "id": s.get("id", "TEST"),
            "realtime_start": s.get("realtime_start", "2024-01-01"),
            "realtime_end": s.get("realtime_end", "2024-01-01"),
            "title": s.get("title", "Test Series"),
            "observation_start": s.get("observation_start", "2020-01-01"),
            "observation_end": s.get("observation_end", "2024-01-01"),
            "frequency": s.get("frequency", "Monthly"),
            "frequency_short": s.get("frequency_short", "M"),
            "units": s.get("units", "Index"),
            "units_short": s.get("units_short", "Index"),
            "seasonal_adjustment": s.get("seasonal_adjustment", "Not Seasonally Adjusted"),
            "seasonal_adjustment_short": s.get("seasonal_adjustment_short", "NSA"),
            "last_updated": s.get("last_updated", "2024-01-01 08:00:00-06"),
            "popularity": s.get("popularity", "50"),
            "notes": s.get("notes", ""),
        }
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        lines.append(f"  <series {attr_str} />")
    series_block = "\n".join(lines)
    return textwrap.dedent(f"""\
<?xml version="1.0" encoding="utf-8" ?>
<seriess realtime_start="2024-01-01" realtime_end="2024-01-01"
         order_by="series_id" sort_order="asc" count="{count}"
         offset="{offset}" limit="{limit}">
{series_block}
</seriess>""")


def make_error_xml(code, message):
    """Generate a FRED error XML response.

    Parameters
    ----------
    code : int
        HTTP error code.
    message : str
        Error message.

    Returns
    -------
    str
    """
    return textwrap.dedent(f"""\
<?xml version="1.0" encoding="utf-8" ?>
<error code="{code}" message="{message}" />""")


# ---------------------------------------------------------------------------
# Sample XML constants
# ---------------------------------------------------------------------------

SAMPLE_GDP_OBSERVATIONS = [
    {"date": "2023-01-01", "value": "26138.0"},
    {"date": "2023-04-01", "value": "26406.2"},
    {"date": "2023-07-01", "value": "26819.7"},
    {"date": "2023-10-01", "value": "27183.9"},
]

SAMPLE_GDP_XML = make_observations_xml(SAMPLE_GDP_OBSERVATIONS)

SAMPLE_CPI_OBSERVATIONS = [
    {"date": "2020-01-01", "value": "257.971"},
    {"date": "2020-02-01", "value": "258.678"},
    {"date": "2020-03-01", "value": "258.115"},
    {"date": "2020-04-01", "value": "256.389"},
    {"date": "2020-05-01", "value": "256.394"},
    {"date": "2020-06-01", "value": "257.797"},
]

SAMPLE_CPI_XML = make_observations_xml(SAMPLE_CPI_OBSERVATIONS)

SAMPLE_PAYEMS_INFO = {
    "id": "PAYEMS",
    "realtime_start": "2024-01-01",
    "realtime_end": "2024-01-01",
    "title": "All Employees: Total Nonfarm Payrolls",
    "observation_start": "1939-01-01",
    "observation_end": "2024-01-01",
    "frequency": "Monthly",
    "frequency_short": "M",
    "units": "Thousands of Persons",
    "units_short": "Thous. of Persons",
    "seasonal_adjustment": "Seasonally Adjusted",
    "seasonal_adjustment_short": "SA",
    "last_updated": "2024-01-05 08:47:20-05",
    "popularity": "86",
    "notes": "All Employees: Total Nonfarm, commonly known as Total Nonfarm Payroll.",
}

SAMPLE_PAYEMS_INFO_XML = make_series_info_xml(SAMPLE_PAYEMS_INFO)

SAMPLE_ALL_RELEASES_OBSERVATIONS = [
    {"date": "2023-10-01", "realtime_start": "2024-01-30", "value": "27183.9"},
    {"date": "2023-10-01", "realtime_start": "2024-02-28", "value": "27200.1"},
    {"date": "2023-10-01", "realtime_start": "2024-03-28", "value": "27220.5"},
    {"date": "2024-01-01", "realtime_start": "2024-04-25", "value": "27560.0"},
]

SAMPLE_ALL_RELEASES_XML = make_observations_xml(SAMPLE_ALL_RELEASES_OBSERVATIONS)

SAMPLE_VINTAGE_DATES = ["2024-01-30", "2024-02-28", "2024-03-28", "2024-04-25"]

SAMPLE_VINTAGE_DATES_XML = make_vintage_dates_xml(SAMPLE_VINTAGE_DATES)

SAMPLE_SEARCH_SERIES = [
    {"id": "GDPC1", "title": "Real Gross Domestic Product", "frequency": "Quarterly",
     "frequency_short": "Q", "units": "Billions of Chained 2017 Dollars",
     "units_short": "Bil. of Chn. 2017 $", "popularity": "95"},
    {"id": "A191RL1Q225SBEA", "title": "Real Gross Domestic Product Growth Rate",
     "frequency": "Quarterly", "frequency_short": "Q", "units": "Percent",
     "units_short": "Pct", "popularity": "80"},
    {"id": "GDP", "title": "Gross Domestic Product", "frequency": "Quarterly",
     "frequency_short": "Q", "units": "Billions of Dollars",
     "units_short": "Bil. of $", "popularity": "90"},
]

SAMPLE_SEARCH_XML = make_search_xml(SAMPLE_SEARCH_SERIES)

SAMPLE_EMPTY_SEARCH_XML = textwrap.dedent("""\
<?xml version="1.0" encoding="utf-8" ?>
<seriess realtime_start="2024-01-01" realtime_end="2024-01-01"
         order_by="series_id" sort_order="asc" count="0"
         offset="0" limit="1000">
</seriess>""")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fred():
    """Create a Fred instance with a test API key."""
    return Fred(api_key="test_key")


@pytest.fixture
def mock_urlopen():
    """Patch fredapi.fred.urlopen and yield the mock."""
    with patch("fredapi.fred.urlopen") as mock_uo:
        yield mock_uo


def set_mock_response(mock_urlopen, xml_string):
    """Configure mock_urlopen to return the given XML string.

    Parameters
    ----------
    mock_urlopen : MagicMock
        The patched urlopen mock.
    xml_string : str
        XML response body.
    """
    mock_urlopen.return_value.read.return_value = xml_string
