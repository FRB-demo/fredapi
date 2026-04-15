"""Demo/synthetic data for when FRED API key is not available."""

import math
import random
from datetime import datetime, timedelta

random.seed(42)

# Cache generated demo data so repeated calls return the same series
_demo_cache: dict[str, dict] = {}


def _generate_monthly_dates(start_year=2015, end_year=2025):
    dates = []
    for y in range(start_year, end_year + 1):
        for m in range(1, 13):
            dates.append(f"{y}-{m:02d}-01")
    return dates


def _generate_quarterly_dates(start_year=2015, end_year=2025):
    dates = []
    for y in range(start_year, end_year + 1):
        for m in [1, 4, 7, 10]:
            dates.append(f"{y}-{m:02d}-01")
    return dates


def _generate_daily_dates(start_year=2020, end_year=2025):
    dates = []
    d = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    while d <= end:
        if d.weekday() < 5:  # weekdays only
            dates.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return dates


def _trend_with_noise(n, start, end, noise=0.02, seasonal_amp=0, seasonal_period=12):
    vals = []
    for i in range(n):
        t = i / max(n - 1, 1)
        base = start + (end - start) * t
        seasonal = seasonal_amp * math.sin(2 * math.pi * i / seasonal_period) if seasonal_period > 0 else 0
        noise_val = random.gauss(0, abs(base) * noise)
        vals.append(round(base + seasonal + noise_val, 2))
    return vals


DEMO_SERIES = {
    "GDP": {
        "dates_fn": lambda: _generate_quarterly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 18000, 29000, noise=0.005),
        "title": "Gross Domestic Product",
        "units": "Billions of Dollars",
        "frequency": "Quarterly",
    },
    "GDPC1": {
        "dates_fn": lambda: _generate_quarterly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 18500, 22500, noise=0.005),
        "title": "Real Gross Domestic Product",
        "units": "Billions of Chained 2017 Dollars",
        "frequency": "Quarterly",
    },
    "A191RL1Q225SBEA": {
        "dates_fn": lambda: _generate_quarterly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 2.5, 2.2, noise=0.5),
        "title": "Real GDP Growth Rate",
        "units": "Percent Change",
        "frequency": "Quarterly",
    },
    "CPIAUCSL": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 237, 315, noise=0.002, seasonal_amp=0.3, seasonal_period=12),
        "title": "Consumer Price Index (All Urban)",
        "units": "Index 1982-1984=100",
        "frequency": "Monthly",
    },
    "CPILFESL": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 244, 320, noise=0.001, seasonal_amp=0.1),
        "title": "Core CPI (Less Food & Energy)",
        "units": "Index 1982-1984=100",
        "frequency": "Monthly",
    },
    "PCEPI": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 100, 128, noise=0.002, seasonal_amp=0.15),
        "title": "PCE Price Index",
        "units": "Index 2017=100",
        "frequency": "Monthly",
    },
    "PCEPILFE": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 100, 125, noise=0.001),
        "title": "Core PCE Price Index",
        "units": "Index 2017=100",
        "frequency": "Monthly",
    },
    "UNRATE": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: [round(max(3.0, min(15.0, v)), 1) for v in _trend_with_noise(n, 5.0, 3.8, noise=0.05, seasonal_amp=0.2)],
        "title": "Unemployment Rate",
        "units": "Percent",
        "frequency": "Monthly",
    },
    "PAYEMS": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 143000, 157000, noise=0.002, seasonal_amp=100),
        "title": "Total Nonfarm Payrolls",
        "units": "Thousands of Persons",
        "frequency": "Monthly",
    },
    "FEDFUNDS": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: [round(max(0.0, v), 2) for v in _trend_with_noise(n, 0.25, 5.25, noise=0.03)],
        "title": "Federal Funds Effective Rate",
        "units": "Percent",
        "frequency": "Monthly",
    },
    "DGS10": {
        "dates_fn": lambda: _generate_daily_dates(),
        "values_fn": lambda n: [round(max(0.5, v), 2) for v in _trend_with_noise(n, 1.8, 4.2, noise=0.02)],
        "title": "10-Year Treasury Constant Maturity Rate",
        "units": "Percent",
        "frequency": "Daily",
    },
    "DGS2": {
        "dates_fn": lambda: _generate_daily_dates(),
        "values_fn": lambda n: [round(max(0.1, v), 2) for v in _trend_with_noise(n, 1.5, 4.5, noise=0.025)],
        "title": "2-Year Treasury Constant Maturity Rate",
        "units": "Percent",
        "frequency": "Daily",
    },
    "T10Y2Y": {
        "dates_fn": lambda: _generate_daily_dates(),
        "values_fn": lambda n: [round(v, 2) for v in _trend_with_noise(n, 0.3, -0.3, noise=0.15)],
        "title": "10-Year Minus 2-Year Treasury Spread",
        "units": "Percent",
        "frequency": "Daily",
    },
    "HOUST": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 1100, 1400, noise=0.04, seasonal_amp=80, seasonal_period=12),
        "title": "Housing Starts",
        "units": "Thousands of Units",
        "frequency": "Monthly",
    },
    "PERMIT": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 1200, 1500, noise=0.03, seasonal_amp=60),
        "title": "Building Permits",
        "units": "Thousands of Units",
        "frequency": "Monthly",
    },
    "CSUSHPINSA": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 175, 310, noise=0.003),
        "title": "Case-Shiller Home Price Index (National)",
        "units": "Index Jan 2000=100",
        "frequency": "Monthly",
    },
    "MSPUS": {
        "dates_fn": lambda: _generate_quarterly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 290000, 420000, noise=0.01),
        "title": "Median Sales Price of Houses Sold",
        "units": "Dollars",
        "frequency": "Quarterly",
    },
    "SP500": {
        "dates_fn": lambda: _generate_daily_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 3200, 5400, noise=0.008),
        "title": "S&P 500 Index",
        "units": "Index",
        "frequency": "Daily",
    },
    "NASDAQCOM": {
        "dates_fn": lambda: _generate_daily_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 9000, 17000, noise=0.01),
        "title": "NASDAQ Composite Index",
        "units": "Index",
        "frequency": "Daily",
    },
    "VIXCLS": {
        "dates_fn": lambda: _generate_daily_dates(),
        "values_fn": lambda n: [round(max(10, v), 2) for v in _trend_with_noise(n, 18, 16, noise=0.15)],
        "title": "CBOE Volatility Index (VIX)",
        "units": "Index",
        "frequency": "Daily",
    },
    "RSAFS": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 450000, 700000, noise=0.01, seasonal_amp=15000, seasonal_period=12),
        "title": "Retail Sales: Total",
        "units": "Millions of Dollars",
        "frequency": "Monthly",
    },
    "INDPRO": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 103, 104, noise=0.005, seasonal_amp=0.5),
        "title": "Industrial Production Index",
        "units": "Index 2017=100",
        "frequency": "Monthly",
    },
    "UMCSENT": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 92, 68, noise=0.04),
        "title": "Consumer Sentiment (U of Michigan)",
        "units": "Index 1966:Q1=100",
        "frequency": "Monthly",
    },
    "DCOILWTICO": {
        "dates_fn": lambda: _generate_daily_dates(),
        "values_fn": lambda n: [round(max(20, v), 2) for v in _trend_with_noise(n, 55, 75, noise=0.03)],
        "title": "Crude Oil Price: WTI",
        "units": "Dollars per Barrel",
        "frequency": "Daily",
    },
    "M2SL": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 12500, 21000, noise=0.003),
        "title": "M2 Money Supply",
        "units": "Billions of Dollars",
        "frequency": "Monthly",
    },
    "DEXUSEU": {
        "dates_fn": lambda: _generate_daily_dates(),
        "values_fn": lambda n: [round(v, 4) for v in _trend_with_noise(n, 1.12, 1.08, noise=0.005)],
        "title": "USD/EUR Exchange Rate",
        "units": "USD per EUR",
        "frequency": "Daily",
    },
    "T10YIE": {
        "dates_fn": lambda: _generate_daily_dates(),
        "values_fn": lambda n: [round(max(0.5, v), 2) for v in _trend_with_noise(n, 1.7, 2.3, noise=0.03)],
        "title": "10-Year Breakeven Inflation Rate",
        "units": "Percent",
        "frequency": "Daily",
    },
    "DFII10": {
        "dates_fn": lambda: _generate_daily_dates(),
        "values_fn": lambda n: [round(v, 2) for v in _trend_with_noise(n, -0.5, 2.0, noise=0.03)],
        "title": "10-Year TIPS Rate",
        "units": "Percent",
        "frequency": "Daily",
    },
    "JTSJOL": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 5800, 8800, noise=0.03),
        "title": "Job Openings: Total Nonfarm",
        "units": "Thousands",
        "frequency": "Monthly",
    },
    "ICSA": {
        "dates_fn": lambda: _generate_monthly_dates(),
        "values_fn": lambda n: _trend_with_noise(n, 220000, 210000, noise=0.05),
        "title": "Initial Jobless Claims",
        "units": "Number",
        "frequency": "Weekly",
    },
}


def get_demo_series(series_id, start_date=None, end_date=None):
    """Generate demo data for a given series ID.
    
    Results are cached so repeated calls with the same series_id return
    identical data. Date filtering is applied after cache lookup.
    """
    # Check cache first for deterministic results
    if series_id not in _demo_cache:
        config = DEMO_SERIES.get(series_id)
        if not config:
            # Generate generic data for unknown series
            dates = _generate_monthly_dates()
            values = _trend_with_noise(len(dates), 100, 120, noise=0.02)
            title = series_id
            units = ""
            frequency = "Monthly"
        else:
            dates = config["dates_fn"]()
            values = config["values_fn"](len(dates))
            title = config["title"]
            units = config["units"]
            frequency = config["frequency"]

        _demo_cache[series_id] = {
            "series_id": series_id,
            "title": title,
            "units": units,
            "frequency": frequency,
            "source": "FRED (Demo)",
            "dates": list(dates),
            "values": list(values),
        }

    # Return a copy with date filters applied
    cached = _demo_cache[series_id]
    dates = list(cached["dates"])
    values = list(cached["values"])

    if start_date:
        filtered = [(d, v) for d, v in zip(dates, values) if d >= start_date]
        if filtered:
            dates, values = zip(*filtered)
            dates, values = list(dates), list(values)

    if end_date:
        filtered = [(d, v) for d, v in zip(dates, values) if d <= end_date]
        if filtered:
            dates, values = zip(*filtered)
            dates, values = list(dates), list(values)

    return {
        "series_id": cached["series_id"],
        "title": cached["title"],
        "units": cached["units"],
        "frequency": cached["frequency"],
        "source": cached["source"],
        "dates": dates,
        "values": values,
    }
