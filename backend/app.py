import math
import os
from datetime import datetime

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from fredapi import Fred

app = FastAPI(title="FRED API Web Application", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_fred() -> Fred:
    """Initialize and return a Fred instance using the FRED_API_KEY env var."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="FRED_API_KEY environment variable is not set. "
            "Please set it to a valid FRED API key.",
        )
    return Fred(api_key=api_key)


def _sanitize_value(val):
    """Convert NaN/Inf float values to None for JSON serialization."""
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


def _series_to_json(series: pd.Series) -> list[dict]:
    """Convert a pandas Series with datetime index to a list of dicts."""
    records = []
    for idx, val in series.items():
        date_str = idx.strftime("%Y-%m-%d") if isinstance(idx, datetime) else str(idx)
        records.append({"date": date_str, "value": _sanitize_value(val)})
    return records


def _dataframe_to_json(df: pd.DataFrame) -> list[dict]:
    """Convert a pandas DataFrame to a list of dicts, handling NaN and datetimes."""
    records = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            val = row[col]
            if isinstance(val, datetime):
                record[col] = val.strftime("%Y-%m-%d")
            elif isinstance(val, pd.Timestamp):
                record[col] = val.strftime("%Y-%m-%d")
            else:
                record[col] = _sanitize_value(val)
        records.append(record)
    return records


def _info_series_to_json(info: pd.Series) -> dict:
    """Convert a pandas Series of metadata to a dict, formatting datetimes."""
    result = {}
    for key, val in info.items():
        if isinstance(val, (datetime, pd.Timestamp)):
            result[key] = val.strftime("%Y-%m-%d")
        else:
            result[key] = _sanitize_value(val)
    return result


@app.get("/api/search")
def search_series(
    q: str = Query(..., description="Search query text"),
    limit: int = Query(1000, ge=1, description="Max number of results"),
    order_by: str | None = Query(None, description="Order results by field"),
    sort_order: str | None = Query(None, description="Sort order: asc or desc"),
):
    """Search for FRED series by text query."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    fred = get_fred()
    try:
        results = fred.search(
            q.strip(),
            limit=limit,
            order_by=order_by,
            sort_order=sort_order,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if results is None or (isinstance(results, pd.DataFrame) and results.empty):
        return {"results": [], "count": 0}

    data = _dataframe_to_json(results)
    return {"results": data, "count": len(data)}


@app.get("/api/series/{series_id}")
def get_series(
    series_id: str,
    observation_start: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    observation_end: str | None = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get observations for a FRED series."""
    fred = get_fred()
    try:
        series = fred.get_series(
            series_id,
            observation_start=observation_start,
            observation_end=observation_end,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    data = _series_to_json(series)
    return {"series_id": series_id, "observations": data}


@app.get("/api/series/{series_id}/info")
def get_series_info(series_id: str):
    """Get metadata for a FRED series."""
    fred = get_fred()
    try:
        info = fred.get_series_info(series_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return _info_series_to_json(info)


@app.get("/api/series/{series_id}/releases")
def get_series_releases(series_id: str):
    """Get all releases (revision history) for a FRED series."""
    fred = get_fred()
    try:
        releases = fred.get_series_all_releases(series_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    data = _dataframe_to_json(releases)
    return {"series_id": series_id, "releases": data}


@app.get("/api/series/{series_id}/vintage-dates")
def get_series_vintage_dates(series_id: str):
    """Get vintage dates for a FRED series."""
    fred = get_fred()
    try:
        dates = fred.get_series_vintage_dates(series_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    formatted = [
        d.strftime("%Y-%m-%d") if isinstance(d, (datetime, pd.Timestamp)) else str(d)
        for d in dates
    ]
    return {"series_id": series_id, "vintage_dates": formatted}


@app.get("/api/series/{series_id}/as-of")
def get_series_as_of(
    series_id: str,
    date: str = Query(..., description="As-of date (YYYY-MM-DD)"),
):
    """Get series data as known on a particular date."""
    fred = get_fred()
    try:
        data = fred.get_series_as_of_date(series_id, date)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    records = _dataframe_to_json(data)
    return {"series_id": series_id, "as_of_date": date, "data": records}
