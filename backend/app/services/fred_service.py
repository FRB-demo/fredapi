"""Service for fetching data from FRED (Federal Reserve Economic Data)."""

import os
import httpx
import pandas as pd
from typing import Optional

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Popular economic series catalog
POPULAR_SERIES = {
    "GDP": {"title": "Gross Domestic Product", "category": "National Accounts", "frequency": "Quarterly", "units": "Billions of Dollars"},
    "GDPC1": {"title": "Real Gross Domestic Product", "category": "National Accounts", "frequency": "Quarterly", "units": "Billions of Chained 2017 Dollars"},
    "CPIAUCSL": {"title": "Consumer Price Index (All Urban)", "category": "Prices", "frequency": "Monthly", "units": "Index 1982-1984=100"},
    "CPILFESL": {"title": "Core CPI (Less Food & Energy)", "category": "Prices", "frequency": "Monthly", "units": "Index 1982-1984=100"},
    "PCEPI": {"title": "PCE Price Index", "category": "Prices", "frequency": "Monthly", "units": "Index 2017=100"},
    "PCEPILFE": {"title": "Core PCE Price Index", "category": "Prices", "frequency": "Monthly", "units": "Index 2017=100"},
    "UNRATE": {"title": "Unemployment Rate", "category": "Labor Market", "frequency": "Monthly", "units": "Percent"},
    "PAYEMS": {"title": "Total Nonfarm Payrolls", "category": "Labor Market", "frequency": "Monthly", "units": "Thousands of Persons"},
    "FEDFUNDS": {"title": "Federal Funds Effective Rate", "category": "Interest Rates", "frequency": "Monthly", "units": "Percent"},
    "DGS10": {"title": "10-Year Treasury Constant Maturity Rate", "category": "Interest Rates", "frequency": "Daily", "units": "Percent"},
    "DGS2": {"title": "2-Year Treasury Constant Maturity Rate", "category": "Interest Rates", "frequency": "Daily", "units": "Percent"},
    "T10Y2Y": {"title": "10-Year Minus 2-Year Treasury Spread", "category": "Interest Rates", "frequency": "Daily", "units": "Percent"},
    "DEXUSEU": {"title": "USD/EUR Exchange Rate", "category": "Exchange Rates", "frequency": "Daily", "units": "USD per EUR"},
    "VIXCLS": {"title": "CBOE Volatility Index (VIX)", "category": "Financial Markets", "frequency": "Daily", "units": "Index"},
    "SP500": {"title": "S&P 500 Index", "category": "Financial Markets", "frequency": "Daily", "units": "Index"},
    "M2SL": {"title": "M2 Money Supply", "category": "Money Supply", "frequency": "Monthly", "units": "Billions of Dollars"},
    "HOUST": {"title": "Housing Starts", "category": "Housing", "frequency": "Monthly", "units": "Thousands of Units"},
    "PERMIT": {"title": "Building Permits", "category": "Housing", "frequency": "Monthly", "units": "Thousands of Units"},
    "CSUSHPINSA": {"title": "Case-Shiller Home Price Index (National)", "category": "Housing", "frequency": "Monthly", "units": "Index Jan 2000=100"},
    "MSPUS": {"title": "Median Sales Price of Houses Sold", "category": "Housing", "frequency": "Quarterly", "units": "Dollars"},
    "RSAFS": {"title": "Retail Sales: Total", "category": "Consumer Spending", "frequency": "Monthly", "units": "Millions of Dollars"},
    "INDPRO": {"title": "Industrial Production Index", "category": "Production", "frequency": "Monthly", "units": "Index 2017=100"},
    "UMCSENT": {"title": "Consumer Sentiment (U of Michigan)", "category": "Surveys", "frequency": "Monthly", "units": "Index 1966:Q1=100"},
    "DCOILWTICO": {"title": "Crude Oil Price: WTI", "category": "Commodities", "frequency": "Daily", "units": "Dollars per Barrel"},
    "NASDAQCOM": {"title": "NASDAQ Composite Index", "category": "Financial Markets", "frequency": "Daily", "units": "Index"},
    "A191RL1Q225SBEA": {"title": "Real GDP Growth Rate", "category": "National Accounts", "frequency": "Quarterly", "units": "Percent Change"},
    "DFII10": {"title": "10-Year TIPS Rate", "category": "Interest Rates", "frequency": "Daily", "units": "Percent"},
    "T10YIE": {"title": "10-Year Breakeven Inflation Rate", "category": "Prices", "frequency": "Daily", "units": "Percent"},
    "JTSJOL": {"title": "Job Openings: Total Nonfarm", "category": "Labor Market", "frequency": "Monthly", "units": "Thousands"},
    "ICSA": {"title": "Initial Jobless Claims", "category": "Labor Market", "frequency": "Weekly", "units": "Number"},
}


async def get_series_data(
    series_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Fetch a single series from FRED API, falling back to demo data if no API key."""
    from app.services.demo_data import get_demo_series

    if not FRED_API_KEY:
        return get_demo_series(series_id, start_date, end_date)

    try:
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
        }
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date

        async with httpx.AsyncClient(timeout=30.0) as client:
            info_resp = await client.get(f"{FRED_BASE_URL}/series", params={
                "series_id": series_id,
                "api_key": FRED_API_KEY,
                "file_type": "json",
            })
            info_data = info_resp.json()
            series_info = info_data.get("seriess", [{}])[0] if info_data.get("seriess") else {}

            obs_resp = await client.get(f"{FRED_BASE_URL}/series/observations", params=params)
            obs_data = obs_resp.json()

        observations = obs_data.get("observations", [])
        dates = []
        values = []
        for obs in observations:
            if obs["value"] != ".":
                dates.append(obs["date"])
                values.append(float(obs["value"]))

        title = series_info.get("title", series_id)
        units = series_info.get("units", "")
        frequency = series_info.get("frequency", "")

        return {
            "series_id": series_id,
            "title": title,
            "units": units,
            "frequency": frequency,
            "source": "FRED",
            "dates": dates,
            "values": values,
        }
    except Exception:
        return get_demo_series(series_id, start_date, end_date)


async def search_series(query: str, limit: int = 20) -> list[dict]:
    """Search for FRED series by keyword."""
    if not FRED_API_KEY:
        # Local search through popular series catalog
        query_lower = query.lower()
        results = []
        for sid, info in POPULAR_SERIES.items():
            if query_lower in sid.lower() or query_lower in info["title"].lower() or query_lower in info["category"].lower():
                results.append({
                    "series_id": sid,
                    "title": info["title"],
                    "frequency": info["frequency"],
                    "units": info["units"],
                    "seasonal_adjustment": "",
                    "last_updated": "",
                    "popularity": 80,
                    "source": "FRED",
                })
        return results[:limit]

    try:
        params = {
            "search_text": query,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "limit": limit,
            "order_by": "popularity",
            "sort_order": "desc",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{FRED_BASE_URL}/series/search", params=params)
            data = resp.json()

        results = []
        for s in data.get("seriess", []):
            results.append({
                "series_id": s["id"],
                "title": s.get("title", ""),
                "frequency": s.get("frequency", ""),
                "units": s.get("units", ""),
                "seasonal_adjustment": s.get("seasonal_adjustment", ""),
                "last_updated": s.get("last_updated", ""),
                "popularity": s.get("popularity", 0),
                "source": "FRED",
            })
        return results
    except Exception:
        return []


def get_popular_series() -> list[dict]:
    """Return the curated list of popular economic series."""
    results = []
    for sid, info in POPULAR_SERIES.items():
        results.append({
            "series_id": sid,
            "title": info["title"],
            "category": info["category"],
            "frequency": info["frequency"],
            "units": info["units"],
            "source": "FRED",
        })
    return results


def get_categories() -> list[str]:
    """Return unique categories from popular series."""
    cats = set()
    for info in POPULAR_SERIES.values():
        cats.add(info["category"])
    return sorted(cats)
