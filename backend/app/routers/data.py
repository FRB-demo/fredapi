"""API router for economic data retrieval."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models import SeriesRequest, MultiSeriesRequest, SearchRequest
from app.services.fred_service import get_series_data, search_series, get_popular_series, get_categories

router = APIRouter()


@router.get("/series/{series_id}")
async def get_series(
    series_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Fetch a single economic data series."""
    try:
        data = await get_series_data(series_id, start_date, end_date)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/multi-series")
async def get_multi_series(request: MultiSeriesRequest):
    """Fetch multiple economic data series."""
    results = []
    errors = []
    for s in request.series:
        try:
            data = await get_series_data(s.series_id, s.start_date, s.end_date)
            results.append(data)
        except Exception as e:
            errors.append({"series_id": s.series_id, "error": str(e)})
    return {"series": results, "errors": errors}


@router.post("/search")
async def search(request: SearchRequest):
    """Search for economic data series."""
    try:
        results = await search_series(request.query, request.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/popular")
async def popular():
    """Get popular economic series."""
    return {"series": get_popular_series()}


@router.get("/categories")
async def categories():
    """Get available data categories."""
    return {"categories": get_categories()}
