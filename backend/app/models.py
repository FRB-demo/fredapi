"""Pydantic models for API request/response schemas."""

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# --- Request Models ---

SERIES_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,30}$")


class SeriesRequest(BaseModel):
    series_id: str
    source: str = "fred"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @field_validator("series_id")
    @classmethod
    def validate_series_id(cls, v: str) -> str:
        """S-10: Validate series_id format."""
        if not SERIES_ID_PATTERN.match(v):
            raise ValueError("series_id must be 1-30 alphanumeric/underscore characters")
        return v


class MultiSeriesRequest(BaseModel):
    series: list[SeriesRequest]


class ForecastRequest(BaseModel):
    series_id: str
    source: str = "fred"
    periods: int = Field(default=12, ge=1, le=120)
    method: str = "auto"
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ChatContextItem(BaseModel):
    """S-12: Validated chat context item."""
    series_id: str
    title: str = ""
    values: list[float | None] = Field(default_factory=list, max_length=5000)
    dates: list[str] = Field(default_factory=list, max_length=5000)
    units: str = ""


class ChatRequest(BaseModel):
    message: str = Field(max_length=2000)
    context: Optional[list[ChatContextItem]] = Field(default=None, max_length=10)


class SearchRequest(BaseModel):
    query: str = Field(max_length=200)
    source: str = "fred"
    limit: int = Field(default=20, ge=1, le=100)


# --- Response Models (B-6) ---

class SeriesResponse(BaseModel):
    series_id: str
    title: str
    units: str
    frequency: str
    source: str
    dates: list[str]
    values: list[float]


class SearchResultItem(BaseModel):
    series_id: str
    title: str
    frequency: str = ""
    units: str = ""
    seasonal_adjustment: str = ""
    last_updated: str = ""
    popularity: int = 0
    source: str = "FRED"


class SearchResponse(BaseModel):
    results: list[SearchResultItem]


class ForecastResponse(BaseModel):
    series_id: str
    title: str
    method: str
    forecast_dates: list[str]
    forecast_values: list[float]
    lower_bound: list[float]
    upper_bound: list[float]
    confidence_level: float
    historical_dates: list[str]
    historical_values: list[float]
    attempted_methods: list[str] = Field(default_factory=list)
    r_squared: Optional[float] = None
    slope: Optional[float] = None


class ChatSuggestedSeries(BaseModel):
    series_id: str
    title: str
    source: str = "FRED"


class ChatResponse(BaseModel):
    response: str
    intent: str
    suggested_series: list[ChatSuggestedSeries] = Field(default_factory=list)


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    name: str
    columns: list[str]
    date_column: Optional[str] = None
    numeric_columns: list[str] = Field(default_factory=list)
    row_count: int
    preview: list[dict]


class DatasetListItem(BaseModel):
    dataset_id: str
    name: str
    columns: list[str]
    date_column: Optional[str] = None
    numeric_columns: list[str] = Field(default_factory=list)
    row_count: int


class HealthResponse(BaseModel):
    status: str
    version: str
    data_mode: str
    environment: str
