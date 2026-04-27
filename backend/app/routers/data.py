"""API router for economic data retrieval."""

import logging
import re

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

import httpx

from app.models import SeriesRequest, MultiSeriesRequest, SearchRequest
from app.services.fred_service import get_series_data, search_series, get_popular_series, get_categories

logger = logging.getLogger("econsight.data")

SERIES_ID_RE = re.compile(r"^[A-Za-z0-9_]{1,30}$")

router = APIRouter()


@router.get("/series/{series_id}")
async def get_series(
    series_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Fetch a single economic data series."""
    if not SERIES_ID_RE.match(series_id):
        raise HTTPException(status_code=400, detail="Invalid series ID format")
    try:
        data = await get_series_data(series_id, start_date, end_date)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError:
        logger.exception("HTTP error fetching series %s", series_id)
        raise HTTPException(status_code=502, detail="Failed to fetch data from upstream provider")
    except Exception:
        logger.exception("Unexpected error fetching series %s", series_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/multi-series")
async def get_multi_series(request: MultiSeriesRequest):
    """Fetch multiple economic data series."""
    results = []
    errors = []
    for s in request.series:
        try:
            data = await get_series_data(s.series_id, s.start_date, s.end_date)
            results.append(data)
        except ValueError as e:
            errors.append({"series_id": s.series_id, "error": str(e)})
        except Exception:
            logger.exception("Error fetching series %s", s.series_id)
            errors.append({"series_id": s.series_id, "error": "Failed to fetch series"})
    return {"series": results, "errors": errors}


@router.post("/search")
async def search(request: SearchRequest):
    """Search for economic data series."""
    try:
        results = await search_series(request.query, request.limit)
        return {"results": results}
    except httpx.HTTPError:
        logger.exception("HTTP error during search")
        raise HTTPException(status_code=502, detail="Search service unavailable")
    except Exception:
        logger.exception("Unexpected error during search")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/popular")
async def popular():
    """Get popular economic series."""
    return {"series": get_popular_series()}


@router.get("/categories")
async def categories():
    """Get available data categories."""
    return {"categories": get_categories()}
