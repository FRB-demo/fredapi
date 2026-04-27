"""Demo/synthetic data for when FRED API key is not available.

Generates deterministic synthetic time series using a dedicated Random instance
so the global random state is not affected (P-5). Data is cached with a size
cap (P-4) derived from the unified indicators catalog (B-7).
"""

import logging
import math
import random
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Optional

from app.config import settings
from app.indicators import CATALOG, CATALOG_BY_ID

logger = logging.getLogger("econsight.demo")

# P-4: LRU-style cache with size cap
_demo_cache: OrderedDict[str, dict] = OrderedDict()
_CACHE_MAX = settings.demo_cache_maxsize


def _cache_put(key: str, value: dict) -> None:
    """Insert into cache, evicting oldest entries if over capacity."""
    _demo_cache[key] = value
    while len(_demo_cache) > _CACHE_MAX:
        _demo_cache.popitem(last=False)


def _generate_monthly_dates(start_year: int = 2015, end_year: int = 2025) -> list[str]:
    """Generate first-of-month dates for the given year range."""
    dates = []
    for y in range(start_year, end_year + 1):
        for m in range(1, 13):
            dates.append(f"{y}-{m:02d}-01")
    return dates


def _generate_quarterly_dates(start_year: int = 2015, end_year: int = 2025) -> list[str]:
    """Generate quarterly dates for the given year range."""
    dates = []
    for y in range(start_year, end_year + 1):
        for m in [1, 4, 7, 10]:
            dates.append(f"{y}-{m:02d}-01")
    return dates


def _generate_daily_dates(start_year: int = 2020, end_year: int = 2025) -> list[str]:
    """Generate weekday-only dates for the given year range."""
    dates = []
    d = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    while d <= end:
        if d.weekday() < 5:
            dates.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return dates


def _make_rng(series_id: str) -> random.Random:
    """Create a per-series seeded RNG for fully deterministic generation."""
    return random.Random(hash(series_id) + 42)


def _trend_with_noise(
    rng: random.Random,
    n: int,
    start: float,
    end: float,
    noise: float = 0.02,
    seasonal_amp: float = 0.0,
    seasonal_period: int = 12,
    clamp_min: float | None = None,
    clamp_max: float | None = None,
    round_digits: int = 2,
) -> list[float]:
    """Generate a trend line with Gaussian noise and optional seasonality."""
    vals = []
    for i in range(n):
        t = i / max(n - 1, 1)
        base = start + (end - start) * t
        seasonal = seasonal_amp * math.sin(2 * math.pi * i / seasonal_period) if seasonal_period > 0 else 0
        noise_val = rng.gauss(0, abs(base) * noise)
        v = base + seasonal + noise_val
        if clamp_min is not None:
            v = max(clamp_min, v)
        if clamp_max is not None:
            v = min(clamp_max, v)
        vals.append(round(v, round_digits))
    return vals


def _generate_from_indicator(ind) -> tuple[list[str], list[float]]:
    """Generate dates and values from an Indicator definition."""
    rng = _make_rng(ind.series_id)
    if ind.demo_dates_type == "quarterly":
        dates = _generate_quarterly_dates()
    elif ind.demo_dates_type == "daily":
        dates = _generate_daily_dates()
    else:
        dates = _generate_monthly_dates()

    values = _trend_with_noise(
        rng,
        len(dates),
        ind.demo_start,
        ind.demo_end,
        noise=ind.demo_noise,
        seasonal_amp=ind.demo_seasonal_amp,
        seasonal_period=ind.demo_seasonal_period,
        clamp_min=ind.demo_value_clamp_min,
        clamp_max=ind.demo_value_clamp_max,
        round_digits=ind.demo_round,
    )
    return dates, values


def get_demo_series(
    series_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Generate demo data for a given series ID.

    Results are cached so repeated calls with the same series_id return
    identical data. Date filtering is applied after cache lookup.
    """
    if series_id not in _demo_cache:
        ind = CATALOG_BY_ID.get(series_id)
        if ind:
            dates, values = _generate_from_indicator(ind)
            title = ind.title
            units = ind.units
            frequency = ind.frequency
        else:
            # P-4: Only cache known series; unknown series get generic data
            logger.debug("Generating generic demo data for unknown series: %s", series_id)
            rng = _make_rng(series_id)
            dates = _generate_monthly_dates()
            values = _trend_with_noise(rng, len(dates), 100, 120, noise=0.02)
            title = series_id
            units = ""
            frequency = "Monthly"

        _cache_put(series_id, {
            "series_id": series_id,
            "title": title,
            "units": units,
            "frequency": frequency,
            "source": "FRED (Demo)",
            "dates": list(dates),
            "values": list(values),
        })

    cached = _demo_cache[series_id]
    dates = list(cached["dates"])
    values = list(cached["values"])

    if start_date:
        filtered = [(d, v) for d, v in zip(dates, values) if d >= start_date]
        dates = [d for d, v in filtered]
        values = [v for d, v in filtered]

    if end_date:
        filtered = [(d, v) for d, v in zip(dates, values) if d <= end_date]
        dates = [d for d, v in filtered]
        values = [v for d, v in filtered]

    return {
        "series_id": cached["series_id"],
        "title": cached["title"],
        "units": cached["units"],
        "frequency": cached["frequency"],
        "source": cached["source"],
        "dates": dates,
        "values": values,
    }
