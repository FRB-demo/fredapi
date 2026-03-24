import sys
import io
import unittest
from unittest import mock
import textwrap
import warnings
import fredapi
import fredapi.fred
from fredapi.exceptions import (
    FredAPIError,
    FredInvalidAPIKeyError,
    FredRateLimitError,
    FredSeriesNotFoundError,
)


# Change here if you want to make actual calls to Fred
# (https://api.stlouisfed.org/fred...)
# Make sure you FRED_API_KEY is set up and internet works.
fake_fred_call = True
fred_api_key = 'secret'
if not fake_fred_call:
    fred_api_key = fredapi.Fred().api_key


class HTTPCall:
    """Encapsulates faked Fred call data."""

    root_url = fredapi.Fred.root_url

    def __init__(self, rel_url, response=None, side_effect=None):
        """Construct HTTPCall from argument.

        Parameters:
        -----------
        rel_url: relative url to the root url for the call.
        response: response to the call if any.
        side_effect: side_effect to the call if any.

        """
        self.url = '{}/{}&api_key={}'.format(self.root_url, rel_url,
                                             fred_api_key)
        self.response = response
        self.side_effect = side_effect


sp500_obs_call = HTTPCall('series/observations?series_id=SP500&{}&{}'.
                          format('observation_start=2014-09-02',
                                 'observation_end=2014-09-05'),
                          response=textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8" ?>
<observations realtime_start="2015-06-28" realtime_end="2015-06-28"
              observation_start="2014-09-02"
              observation_end="2014-09-05" units="lin"
              output_type="1" file_type="xml"
              order_by="observation_date" sort_order="asc"
              count="4" offset="0" limit="100000">
  <observation realtime_start="2015-06-28" realtime_end="2015-06-28"
               date="2014-09-02" value="2002.28"/>
  <observation realtime_start="2015-06-28" realtime_end="2015-06-28"
               date="2014-09-03" value="2000.72"/>
  <observation realtime_start="2015-06-28" realtime_end="2015-06-28"
               date="2014-09-04" value="1997.65"/>
  <observation realtime_start="2015-06-28" realtime_end="2015-06-28"
               date="2014-09-05" value="2007.71"/>
</observations>'''))
search_call = HTTPCall('release/series?release_id=175&' +
                       'order_by=series_id&sort_order=asc',
                       response=textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8"?>
<seriess realtime_start="2015-07-19" realtime_end="2015-07-19"
         order_by="series_id" sort_order="asc" count="6164"
         offset="0" limit="1000">
  <series id="PCPI01001" realtime_start="2015-07-19" realtime_end="2015-07-19"
          title="Per Capita Personal Income in Autauga County, AL"
          observation_start="1969-01-01" observation_end="2013-01-01"
          frequency="Annual" frequency_short="A" units="Dollars"
          units_short="$" seasonal_adjustment="Not Seasonally Adjusted"
          seasonal_adjustment_short="NSA" last_updated="2015-01-29 12:10:21-06"
          popularity="0" notes="..." />
  <series id="PCPI01003" realtime_start="2015-07-19" realtime_end="2015-07-19"
          title="Per Capita Personal Income in Baldwin County, AL"
          observation_start="1969-01-01" observation_end="2013-01-01"
          frequency="Annual" frequency_short="A" units="Dollars"
          units_short="$" seasonal_adjustment="Not Seasonally Adjusted"
          seasonal_adjustment_short="NSA" last_updated="2015-01-29 12:10:21-06"
          popularity="0" notes="..." />
  <series id="PCPI01005" realtime_start="2015-07-19" realtime_end="2015-07-19"
          title="Per Capita Personal Income in Barbour County, AL"
          observation_start="1969-01-01" observation_end="2013-01-01"
          frequency="Annual" frequency_short="A" units="Dollars"
          units_short="$" seasonal_adjustment="Not Seasonally Adjusted"
          seasonal_adjustment_short="NSA" last_updated="2015-01-29 12:10:21-06"
          popularity="0" notes="..." />
  <!-- more series come here, but not useful for the test... -->
</seriess>
'''))
payems_info_call = HTTPCall('series?series_id=PAYEMS',
                            response=textwrap.dedent('''\
<?xml version="1.0" encoding="utf-8" ?>
<seriess realtime_start="2015-06-28" realtime_end="2015-06-28">
  <series id="PAYEMS" realtime_start="2015-06-28"
          realtime_end="2015-06-28"
          title="All Employees: Total Nonfarm Payrolls"
          observation_start="1939-01-01"
          observation_end="2015-05-01"
          frequency="Monthly" frequency_short="M"
          units="Thousands of Persons"
          units_short="Thous. of Persons"
          seasonal_adjustment="Seasonally Adjusted"
          seasonal_adjustment_short="SA"
          last_updated="2015-06-05 08:47:20-05"
          popularity="86" notes="..." />
</seriess>'''))


class TestFred(unittest.TestCase):

    """Test fredapi.Fred class.

    See setUp() to configure the tests to make internent requests or fake.

    """

    root_url = fredapi.Fred.root_url

    def setUp(self):
        """Set up test.

        If the FRED_API_KEY env variable is defined, we use it in the url to
        help with quick checks between what's expected and what's returned by
        Fred.

        Only go against Fred during tests if fake_fred_call variable is True.

        as results are subject to change and the tests should be runnable
        without an internet connection or a FRED api key so they can be
        run as part of automated continuous integration (e.g. travis-ci.org).

        """
        self.fred = fredapi.Fred(api_key=fred_api_key, proxies=None)
        self.fake_fred_call = fake_fred_call
        self.__original_urlopen = fredapi.fred.urlopen

    def tearDown(self):
        """Cleanup."""
        pass

    def prepare_urlopen(self, urlopen, http_response=None, side_effect=None):
        """Set urlopen to return http_response or the regular call."""
        if self.fake_fred_call:
            if http_response:
                urlopen.return_value.read.return_value = http_response
            elif side_effect:
                urlopen.return_value.read.side_effect = side_effect
        else:
            urlopen.side_effect = self.__original_urlopen

    @mock.patch('fredapi.fred.urlopen')
    def test_get_series(self, urlopen):
        """Test retrieval of series for SP500."""
        self.prepare_urlopen(urlopen,
                             http_response=sp500_obs_call.response)
        serie = self.fred.get_series('SP500', observation_start='9/2/2014',
                                     observation_end='9/5/2014')
        urlopen.assert_called_with(sp500_obs_call.url)
        self.assertEqual(serie.loc['9/2/2014'], 2002.28)
        self.assertEqual(len(serie), 4)

    @mock.patch('fredapi.fred.urlopen')
    def test_get_series_info_payem(self, urlopen):
        """Test retrieval of get_series_info for PAYEMS."""
        url = payems_info_call.url
        http_response = payems_info_call.response
        self.prepare_urlopen(urlopen, http_response=http_response)
        info = self.fred.get_series_info('PAYEMS')
        urlopen.assert_called_with(url)
        self.assertEqual(info['title'], 'All Employees: Total Nonfarm Payrolls')
        self.assertEqual(info['frequency'], 'Monthly')
        self.assertEqual(info['frequency_short'], 'M')

    @mock.patch('fredapi.fred.urlopen')
    def test_invalid_id_in_get_series(self, urlopen):
        """Test invalid series id in get_series."""
        url = ('{}/series/observations?series_id=invalid&api_key={}'.
               format(self.root_url, fred_api_key))
        # some of the argument cannot be mocked easily.
        error = textwrap.dedent('''\
                <?xml version="1.0" encoding="utf-8" ?>
                <error code="400" message="Bad Request.
                The series does not exist." />\n\n\n\n
                ''')
        fp = io.StringIO(error)
        side_effect = fredapi.fred.HTTPError(url, 400, '', '', fp)
        self.prepare_urlopen(urlopen, side_effect=side_effect)
        with self.assertRaises(FredSeriesNotFoundError):
            self.fred.get_series('invalid')
        urlopen.assert_called_with(url)

    @mock.patch('fredapi.fred.urlopen')
    def test_invalid_id_in_get_series_info(self, urlopen):
        """Test invalid series id in get_series_info."""
        url = '{}/series?series_id=invalid&api_key={}'.format(self.root_url,
                                                              fred_api_key)
        error_msg = 'Bad Request.  The series does not exist.'
        # some of the argument cannot be mocked easily.
        xml_error = textwrap.dedent('''\
        <?xml version="1.0" encoding="utf-8" ?>
        <error code="400" message="{}" />\n\n\n
        '''.format(error_msg))
        fp = io.StringIO(xml_error)
        side_effect = fredapi.fred.HTTPError(url, 400, 'Bad Request', '', fp)
        self.prepare_urlopen(urlopen, side_effect=side_effect)
        with self.assertRaises(FredSeriesNotFoundError) as context:
            self.fred.get_series_info('invalid')
        self.assertEqual(str(context.exception), error_msg)
        urlopen.assert_called_with(url)

    @mock.patch('fredapi.fred.urlopen')
    def test_invalid_kwarg_in_get_series(self, urlopen):
        """Test invalid keyword argument in call to get_series."""
        url = '{}/series?series_id=invalid&api_key={}'.format(self.root_url,
                                                              fred_api_key)
        side_effect = fredapi.fred.HTTPError(url, 400, '', '', sys.stderr)
        self.prepare_urlopen(urlopen, side_effect=side_effect)
        with self.assertRaises(ValueError) as context:
            self.fred.get_series('SP500',
                                 observation_start='invalid-datetime-str')
        self.assertFalse(urlopen.called)

    @unittest.skip('Not sure why this crashes in some environments, skipping')
    @mock.patch('fredapi.fred.urlopen')
    def test_search(self, urlopen):
        """Simple test to check retrieval of series info."""
        self.prepare_urlopen(urlopen, http_response=search_call.response)
        pi_series = self.fred.search_by_release(175, limit=3,
                                                order_by='series_id',
                                                sort_order='asc')
        urlopen.assert_called_with(search_call.url)
        actual = str(pi_series[['popularity', 'observation_start',
                                'seasonal_adjustment_short']])
        expected = textwrap.dedent('''\
                  popularity observation_start seasonal_adjustment_short
        series id
        PCPI01001          0        1969-01-01                       NSA
        PCPI01003          0        1969-01-01                       NSA
        PCPI01005          0        1969-01-01                       NSA''')
        for aline, eline in zip(actual.split('\n'), expected.split('\n')):
            self.assertEqual(aline.strip(), eline.strip())


class TestFredExceptions(unittest.TestCase):
    """Test custom exception classes and error handling."""

    root_url = fredapi.Fred.root_url

    def setUp(self):
        self.fred = fredapi.Fred(api_key='secret', proxies=None)
        self.__original_urlopen = fredapi.fred.urlopen

    @mock.patch('fredapi.fred.urlopen')
    def test_fred_api_error_on_non_xml_error_body(self, urlopen):
        """Test that non-XML error responses produce FredAPIError."""
        non_xml_body = b'This is not valid XML <<<>>>'
        exc = fredapi.fred.HTTPError(
            'http://example.com', 503, 'Service Unavailable', {}, io.BytesIO(b'')
        )
        exc.read = mock.Mock(return_value=non_xml_body)
        exc.code = 503
        urlopen.side_effect = exc
        with self.assertRaises(FredAPIError) as context:
            self.fred.get_series_info('TEST')
        self.assertEqual(context.exception.code, 503)
        self.assertIn('503', str(context.exception))

    @mock.patch('fredapi.fred.urlopen')
    def test_fred_rate_limit_error(self, urlopen):
        """Test that HTTP 429 raises FredRateLimitError."""
        error_xml = b'<?xml version="1.0" encoding="utf-8" ?><error code="429" message="Rate limit exceeded." />'
        exc = fredapi.fred.HTTPError(
            'http://example.com', 429, 'Too Many Requests', {}, io.BytesIO(b'')
        )
        exc.read = mock.Mock(return_value=error_xml)
        exc.code = 429
        urlopen.side_effect = exc
        with self.assertRaises(FredRateLimitError) as context:
            self.fred.get_series_info('GDP')
        self.assertEqual(context.exception.code, 429)
        self.assertIn('Rate limit', str(context.exception))

    @mock.patch('fredapi.fred.urlopen')
    def test_fred_invalid_api_key_error(self, urlopen):
        """Test that HTTP 401 raises FredInvalidAPIKeyError."""
        error_xml = b'<?xml version="1.0" encoding="utf-8" ?><error code="401" message="Invalid API key." />'
        exc = fredapi.fred.HTTPError(
            'http://example.com', 401, 'Unauthorized', {}, io.BytesIO(b'')
        )
        exc.read = mock.Mock(return_value=error_xml)
        exc.code = 401
        urlopen.side_effect = exc
        with self.assertRaises(FredInvalidAPIKeyError) as context:
            self.fred.get_series_info('GDP')
        self.assertEqual(context.exception.code, 401)

    @mock.patch('fredapi.fred.urlopen')
    def test_fred_series_not_found_error(self, urlopen):
        """Test that series-not-found returns FredSeriesNotFoundError."""
        error_xml = b'<?xml version="1.0" encoding="utf-8" ?><error code="400" message="Bad Request. The series does not exist." />'
        exc = fredapi.fred.HTTPError(
            'http://example.com', 400, 'Bad Request', {}, io.BytesIO(b'')
        )
        exc.read = mock.Mock(return_value=error_xml)
        exc.code = 400
        urlopen.side_effect = exc
        with self.assertRaises(FredSeriesNotFoundError):
            self.fred.get_series('INVALID')

    @mock.patch('fredapi.fred.urlopen')
    def test_xml_parse_error_on_response(self, urlopen):
        """Test that invalid XML in a successful response raises ValueError with message."""
        urlopen.return_value.read.return_value = b'NOT VALID XML <<>>'
        with self.assertRaises(ValueError) as context:
            self.fred.get_series_info('GDP')
        self.assertIn('Failed to parse FRED response as XML', str(context.exception))

    @mock.patch('fredapi.fred.urlopen')
    def test_exception_hierarchy(self, urlopen):
        """Test that custom exceptions inherit correctly."""
        error_xml = b'<?xml version="1.0" encoding="utf-8" ?><error code="429" message="Rate limit exceeded." />'
        exc = fredapi.fred.HTTPError(
            'http://example.com', 429, 'Too Many Requests', {}, io.BytesIO(b'')
        )
        exc.read = mock.Mock(return_value=error_xml)
        exc.code = 429
        urlopen.side_effect = exc
        with self.assertRaises(fredapi.FredError):
            self.fred.get_series_info('GDP')

    @mock.patch('fredapi.fred.urlopen')
    def test_no_pandas_deprecation_warnings(self, urlopen):
        """Test that _parse does not emit deprecation warnings."""
        obs_response = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8" ?>
            <observations count="1" offset="0" limit="100000">
              <observation realtime_start="2024-01-01" realtime_end="2024-01-01"
                           date="2024-01-01" value="100.0"/>
            </observations>""")
        urlopen.return_value.read.return_value = obs_response
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            self.fred.get_series('TEST')
            pandas_warnings = [x for x in w if 'deprecat' in str(x.message).lower()
                               and 'pandas' in str(x.category.__module__).lower()]
            self.assertEqual(len(pandas_warnings), 0,
                             "Unexpected pandas deprecation warnings: %s" % pandas_warnings)

    def test_exceptions_exported_from_package(self):
        """Test that exception classes are accessible from the fredapi package."""
        self.assertTrue(hasattr(fredapi, 'FredError'))
        self.assertTrue(hasattr(fredapi, 'FredAPIError'))
        self.assertTrue(hasattr(fredapi, 'FredSeriesNotFoundError'))
        self.assertTrue(hasattr(fredapi, 'FredRateLimitError'))
        self.assertTrue(hasattr(fredapi, 'FredInvalidAPIKeyError'))


if __name__ == '__main__':
    unittest.main()
