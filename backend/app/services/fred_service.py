"""Service for fetching data from FRED (Federal Reserve Economic Data)."""

import asyncio
import logging
from typing import Optional

import httpx
from cachetools import TTLCache

from app.config import settings
from app.indicators import POPULAR_SERIES

logger = logging.getLogger("econsight.fred")

FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Shared HTTP client for connection pooling and reuse (P-1)
_http_client: httpx.AsyncClient | None = None

# TTL cache for FRED API responses (P-3)
_series_cache: TTLCache = TTLCache(maxsize=settings.fred_cache_maxsize, ttl=settings.fred_cache_ttl)


def _get_http_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


def _sanitize_error(error: Exception) -> str:
    """S-4: Sanitize exception messages to avoid leaking the API key."""
    msg = str(error)
    api_key = settings.fred_api_key
    if api_key and api_key in msg:
        msg = msg.replace(api_key, "***")
    return msg


async def get_series_data(
    series_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Fetch a single series from FRED API, falling back to demo data if no API key."""
    from app.services.demo_data import get_demo_series

    if not settings.fred_api_key:
        return get_demo_series(series_id, start_date, end_date)

    # P-3: Check cache first
    cache_key = (series_id, start_date, end_date)
    if cache_key in _series_cache:
        logger.debug("Cache hit for %s", series_id)
        return _series_cache[cache_key]

    try:
        params = {
            "series_id": series_id,
            "api_key": settings.fred_api_key,
            "file_type": "json",
        }
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date

        client = _get_http_client()
        info_resp, obs_resp = await asyncio.gather(
            client.get(f"{FRED_BASE_URL}/series", params={
                "series_id": series_id,
                "api_key": settings.fred_api_key,
                "file_type": "json",
            }),
            client.get(f"{FRED_BASE_URL}/series/observations", params=params),
        )
        info_resp.raise_for_status()
        obs_resp.raise_for_status()
        info_data = info_resp.json()
        series_info = info_data.get("seriess", [{}])[0] if info_data.get("seriess") else {}
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

        result = {
            "series_id": series_id,
            "title": title,
            "units": units,
            "frequency": frequency,
            "source": "FRED",
            "dates": dates,
            "values": values,
        }

        # P-3: Cache the result
        _series_cache[cache_key] = result
        return result

    except httpx.HTTPError as e:
        logger.warning("FRED API HTTP error for %s: %s", series_id, _sanitize_error(e))
        return get_demo_series(series_id, start_date, end_date)
    except Exception as e:
        logger.warning("FRED API error for %s: %s", series_id, _sanitize_error(e))
        return get_demo_series(series_id, start_date, end_date)


async def search_series(query: str, limit: int = 20) -> list[dict]:
    """Search for FRED series by keyword."""
    if not settings.fred_api_key:
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
            "api_key": settings.fred_api_key,
            "file_type": "json",
            "limit": limit,
            "order_by": "popularity",
            "sort_order": "desc",
        }

        client = _get_http_client()
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
    except httpx.HTTPError:
        logger.exception("FRED search HTTP error")
        return []
    except Exception:
        logger.exception("FRED search error")
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
