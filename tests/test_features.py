"""Tests for new features: get_multiple_series, tags API, citation, vintage dates enhancement, timeout."""

import sys
import textwrap
from datetime import date
from unittest import mock

import pytest
import pandas as pd

import fredapi
import fredapi.fred


FRED_API_KEY = 'testkey'
ROOT_URL = fredapi.Fred.root_url


def make_fred():
    return fredapi.Fred(api_key=FRED_API_KEY)


# ---------------------------------------------------------------------------
# Mock XML responses
# ---------------------------------------------------------------------------

GDP_OBS_XML = textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8" ?>
<observations count="3" offset="0" limit="100000">
  <observation date="2023-01-01" value="26138.5"/>
  <observation date="2023-04-01" value="26466.2"/>
  <observation date="2023-07-01" value="26998.5"/>
</observations>''')

UNRATE_OBS_XML = textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8" ?>
<observations count="3" offset="0" limit="100000">
  <observation date="2023-01-01" value="3.4"/>
  <observation date="2023-04-01" value="3.5"/>
  <observation date="2023-07-01" value="3.6"/>
</observations>''')

CPIAUCSL_OBS_XML = textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8" ?>
<observations count="2" offset="0" limit="100000">
  <observation date="2023-01-01" value="300.5"/>
  <observation date="2023-04-01" value="302.1"/>
</observations>''')

TAGS_XML = textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8" ?>
<tags realtime_start="2023-01-01" realtime_end="2023-12-31" count="2" offset="0" limit="1000">
  <tag name="gdp" group_id="1" notes="Gross Domestic Product" created="2012-02-27" popularity="95" series_count="100"/>
  <tag name="quarterly" group_id="2" notes="" created="2012-02-27" popularity="80" series_count="200"/>
</tags>''')

RELATED_TAGS_XML = textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8" ?>
<tags realtime_start="2023-01-01" realtime_end="2023-12-31" count="1" offset="0" limit="1000">
  <tag name="annual" group_id="2" notes="" created="2012-02-27" popularity="70" series_count="150"/>
</tags>''')

SERIES_BY_TAG_XML = textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8" ?>
<seriess realtime_start="2023-01-01" realtime_end="2023-12-31" count="1" offset="0" limit="1000">
  <series id="GDP" realtime_start="2023-01-01" realtime_end="2023-12-31"
          title="Gross Domestic Product"
          observation_start="1947-01-01" observation_end="2023-07-01"
          frequency="Quarterly" frequency_short="Q" units="Billions of Dollars"
          units_short="Bil. of $" seasonal_adjustment="Seasonally Adjusted"
          seasonal_adjustment_short="SA" last_updated="2023-10-26 07:56:03-05"
          popularity="95" notes="GDP measures total output." />
</seriess>''')

GDP_INFO_XML = textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8" ?>
<seriess realtime_start="2023-01-01" realtime_end="2023-12-31">
  <series id="GDP" realtime_start="2023-01-01" realtime_end="2023-12-31"
          title="Gross Domestic Product"
          observation_start="1947-01-01" observation_end="2023-07-01"
          frequency="Quarterly" frequency_short="Q" units="Billions of Dollars"
          units_short="Bil. of $" seasonal_adjustment="Seasonally Adjusted"
          seasonal_adjustment_short="SA" last_updated="2023-10-26 07:56:03-05"
          popularity="95" notes="GDP measures total output." />
</seriess>''')

VINTAGE_DATES_XML = textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8" ?>
<vintage_dates realtime_start="2023-01-01" realtime_end="2023-12-31" count="3">
  <vintage_date>2023-01-27</vintage_date>
  <vintage_date>2023-02-23</vintage_date>
  <vintage_date>2023-03-30</vintage_date>
</vintage_dates>''')

VINTAGE_DATES_DESC_XML = textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8" ?>
<vintage_dates realtime_start="2023-01-01" realtime_end="2023-06-30" count="2">
  <vintage_date>2023-03-30</vintage_date>
  <vintage_date>2023-02-23</vintage_date>
</vintage_dates>''')


# ---------------------------------------------------------------------------
# Helper: create a mock response object
# ---------------------------------------------------------------------------

def mock_urlopen_response(xml_bytes):
    """Return a mock response whose .read() returns the given XML string."""
    resp = mock.MagicMock()
    if isinstance(xml_bytes, str):
        xml_bytes = xml_bytes.encode('utf-8')
    resp.read.return_value = xml_bytes
    return resp


# ===========================================================================
# Tests for get_multiple_series
# ===========================================================================

class TestGetMultipleSeries:

    @mock.patch('fredapi.fred.urlopen')
    def test_multiple_series_basic(self, mock_urlopen):
        """Fetch two series and verify DataFrame shape."""
        def side_effect(url, timeout=30):
            if 'series_id=GDP' in url:
                return mock_urlopen_response(GDP_OBS_XML)
            elif 'series_id=UNRATE' in url:
                return mock_urlopen_response(UNRATE_OBS_XML)
            raise ValueError('Unexpected URL: ' + url)

        mock_urlopen.side_effect = side_effect
        fred = make_fred()
        df = fred.get_multiple_series(['GDP', 'UNRATE'])

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ['GDP', 'UNRATE']
        assert len(df) == 3  # 3 dates

    @mock.patch('fredapi.fred.urlopen')
    def test_multiple_series_three(self, mock_urlopen):
        """Fetch three series."""
        def side_effect(url, timeout=30):
            if 'series_id=GDP' in url:
                return mock_urlopen_response(GDP_OBS_XML)
            elif 'series_id=UNRATE' in url:
                return mock_urlopen_response(UNRATE_OBS_XML)
            elif 'series_id=CPIAUCSL' in url:
                return mock_urlopen_response(CPIAUCSL_OBS_XML)
            raise ValueError('Unexpected URL: ' + url)

        mock_urlopen.side_effect = side_effect
        fred = make_fred()
        df = fred.get_multiple_series(['GDP', 'CPIAUCSL', 'UNRATE'])

        assert list(df.columns) == ['GDP', 'CPIAUCSL', 'UNRATE']
        assert len(df) == 3  # union of dates

    @mock.patch('fredapi.fred.urlopen')
    def test_multiple_series_with_failure(self, mock_urlopen):
        """One series fails; should still return the other with NaN column."""
        def side_effect(url, timeout=30):
            if 'series_id=GDP' in url:
                return mock_urlopen_response(GDP_OBS_XML)
            elif 'series_id=INVALID' in url:
                raise ValueError('Bad series')
            raise ValueError('Unexpected URL: ' + url)

        mock_urlopen.side_effect = side_effect
        fred = make_fred()
        df = fred.get_multiple_series(['GDP', 'INVALID'])

        assert 'GDP' in df.columns
        assert 'INVALID' in df.columns
        # INVALID column should be empty (NaN)
        assert df['INVALID'].dropna().empty

    def test_multiple_series_empty_list(self):
        """Empty list returns empty DataFrame."""
        fred = make_fred()
        df = fred.get_multiple_series([])
        assert isinstance(df, pd.DataFrame)
        assert df.empty


# ===========================================================================
# Tests for Tags API
# ===========================================================================

class TestTagsAPI:

    @mock.patch('fredapi.fred.urlopen')
    def test_get_tags(self, mock_urlopen):
        """Basic get_tags call."""
        mock_urlopen.return_value = mock_urlopen_response(TAGS_XML)
        fred = make_fred()
        tags = fred.get_tags()

        assert isinstance(tags, pd.DataFrame)
        assert len(tags) == 2
        assert 'name' in tags.columns
        assert tags.iloc[0]['name'] == 'gdp'

    @mock.patch('fredapi.fred.urlopen')
    def test_get_tags_with_kwargs(self, mock_urlopen):
        """get_tags with extra kwargs should include them in URL."""
        mock_urlopen.return_value = mock_urlopen_response(TAGS_XML)
        fred = make_fred()
        fred.get_tags(limit=10, order_by='popularity')

        called_url = mock_urlopen.call_args[0][0]
        assert 'limit=10' in called_url
        assert 'order_by=popularity' in called_url

    @mock.patch('fredapi.fred.urlopen')
    def test_get_related_tags_string(self, mock_urlopen):
        """get_related_tags with a single string."""
        mock_urlopen.return_value = mock_urlopen_response(RELATED_TAGS_XML)
        fred = make_fred()
        tags = fred.get_related_tags('gdp')

        assert isinstance(tags, pd.DataFrame)
        assert len(tags) == 1
        assert tags.iloc[0]['name'] == 'annual'
        called_url = mock_urlopen.call_args[0][0]
        assert 'tag_names=gdp' in called_url

    @mock.patch('fredapi.fred.urlopen')
    def test_get_related_tags_list(self, mock_urlopen):
        """get_related_tags with a list of tags joins with semicolons."""
        mock_urlopen.return_value = mock_urlopen_response(RELATED_TAGS_XML)
        fred = make_fred()
        fred.get_related_tags(['monetary aggregates', 'weekly'])

        called_url = mock_urlopen.call_args[0][0]
        assert 'tag_names=monetary+aggregates%3Bweekly' in called_url or \
               'tag_names=monetary%20aggregates%3Bweekly' in called_url

    @mock.patch('fredapi.fred.urlopen')
    def test_get_series_by_tag(self, mock_urlopen):
        """get_series_by_tag returns a DataFrame of matching series."""
        mock_urlopen.return_value = mock_urlopen_response(SERIES_BY_TAG_XML)
        fred = make_fred()
        data = fred.get_series_by_tag('gdp')

        assert isinstance(data, pd.DataFrame)
        assert 'GDP' in data.index


# ===========================================================================
# Tests for get_series_citation
# ===========================================================================

class TestGetSeriesCitation:

    @mock.patch('fredapi.fred.urlopen')
    def test_citation_format(self, mock_urlopen):
        """Citation string should contain title, series_id, and today's date."""
        mock_urlopen.return_value = mock_urlopen_response(GDP_INFO_XML)
        fred = make_fred()
        citation = fred.get_series_citation('GDP')

        today_str = date.today().strftime('%B %d, %Y')
        assert 'Gross Domestic Product' in citation
        assert '[GDP]' in citation
        assert 'Federal Reserve Bank of St. Louis' in citation
        assert 'https://fred.stlouisfed.org/series/GDP' in citation
        assert today_str in citation


# ===========================================================================
# Tests for get_series_vintage_dates enhancement
# ===========================================================================

class TestGetSeriesVintageDates:

    @mock.patch('fredapi.fred.urlopen')
    def test_vintage_dates_basic(self, mock_urlopen):
        """Basic call without optional params."""
        mock_urlopen.return_value = mock_urlopen_response(VINTAGE_DATES_XML)
        fred = make_fred()
        dates = fred.get_series_vintage_dates('GDP')

        assert len(dates) == 3

    @mock.patch('fredapi.fred.urlopen')
    def test_vintage_dates_with_realtime_start(self, mock_urlopen):
        """realtime_start is included in URL."""
        mock_urlopen.return_value = mock_urlopen_response(VINTAGE_DATES_XML)
        fred = make_fred()
        fred.get_series_vintage_dates('GDP', realtime_start='2023-01-01')

        called_url = mock_urlopen.call_args[0][0]
        assert 'realtime_start=2023-01-01' in called_url

    @mock.patch('fredapi.fred.urlopen')
    def test_vintage_dates_with_realtime_end(self, mock_urlopen):
        """realtime_end is included in URL."""
        mock_urlopen.return_value = mock_urlopen_response(VINTAGE_DATES_XML)
        fred = make_fred()
        fred.get_series_vintage_dates('GDP', realtime_end='2023-06-30')

        called_url = mock_urlopen.call_args[0][0]
        assert 'realtime_end=2023-06-30' in called_url

    @mock.patch('fredapi.fred.urlopen')
    def test_vintage_dates_sort_order_desc(self, mock_urlopen):
        """sort_order=desc is included in URL."""
        mock_urlopen.return_value = mock_urlopen_response(VINTAGE_DATES_DESC_XML)
        fred = make_fred()
        dates = fred.get_series_vintage_dates('GDP', sort_order='desc')

        called_url = mock_urlopen.call_args[0][0]
        assert 'sort_order=desc' in called_url
        assert len(dates) == 2

    def test_vintage_dates_invalid_sort_order(self):
        """Invalid sort_order raises ValueError."""
        fred = make_fred()
        with pytest.raises(ValueError, match="sort_order must be"):
            fred.get_series_vintage_dates('GDP', sort_order='invalid')

    @mock.patch('fredapi.fred.urlopen')
    def test_vintage_dates_all_params(self, mock_urlopen):
        """All optional params in URL."""
        mock_urlopen.return_value = mock_urlopen_response(VINTAGE_DATES_DESC_XML)
        fred = make_fred()
        fred.get_series_vintage_dates('GDP', realtime_start='2023-01-01',
                                      realtime_end='2023-06-30', sort_order='desc')

        called_url = mock_urlopen.call_args[0][0]
        assert 'realtime_start=2023-01-01' in called_url
        assert 'realtime_end=2023-06-30' in called_url
        assert 'sort_order=desc' in called_url


# ===========================================================================
# Tests for timeout parameter
# ===========================================================================

class TestTimeout:

    def test_default_timeout(self):
        """Default timeout is 30."""
        fred = make_fred()
        assert fred.timeout == 30

    def test_custom_timeout(self):
        """Custom timeout is stored."""
        fred = fredapi.Fred(api_key=FRED_API_KEY, timeout=60)
        assert fred.timeout == 60

    @mock.patch('fredapi.fred.urlopen')
    def test_timeout_passed_to_urlopen(self, mock_urlopen):
        """Timeout is passed to urlopen."""
        mock_urlopen.return_value = mock_urlopen_response(GDP_INFO_XML)
        fred = fredapi.Fred(api_key=FRED_API_KEY, timeout=45)
        fred.get_series_info('GDP')

        # Check that urlopen was called with timeout=45
        _, kwargs = mock_urlopen.call_args
        assert kwargs.get('timeout') == 45

    @mock.patch('fredapi.fred.urlopen')
    def test_default_timeout_passed_to_urlopen(self, mock_urlopen):
        """Default timeout (30) is passed to urlopen."""
        mock_urlopen.return_value = mock_urlopen_response(GDP_INFO_XML)
        fred = make_fred()
        fred.get_series_info('GDP')

        _, kwargs = mock_urlopen.call_args
        assert kwargs.get('timeout') == 30
