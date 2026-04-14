"""Pydantic models for API request/response schemas."""

from typing import Optional
from pydantic import BaseModel


class SeriesRequest(BaseModel):
    series_id: str
    source: str = "fred"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class MultiSeriesRequest(BaseModel):
    series: list[SeriesRequest]


class ForecastRequest(BaseModel):
    series_id: str
    source: str = "fred"
    periods: int = 12
    method: str = "auto"
    confidence_level: float = 0.95
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    context: Optional[list[dict]] = None


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    name: str
    columns: list[str]
    row_count: int
    preview: list[dict]


class SearchRequest(BaseModel):
    query: str
    source: str = "fred"
    limit: int = 20
