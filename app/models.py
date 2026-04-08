"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request body for the /api/query endpoint."""

    question: str = Field(..., min_length=1, description="The question to ask")
    sources: Optional[List[str]] = Field(
        default=None, description="List of source names to filter by"
    )
    top_k: int = Field(default=10, ge=1, le=50, description="Number of chunks to retrieve")


class CitationResponse(BaseModel):
    """A citation from a source document."""

    source_name: str
    source_url: str
    text_snippet: str
    date: Optional[str] = None


class QueryResponse(BaseModel):
    """Response body for the /api/query endpoint."""

    answer: str
    citations: List[CitationResponse] = []


class SourceInfo(BaseModel):
    """Metadata about a registered data source."""

    name: str
    display_name: str
    base_url: str
    doc_type: str
    healthy: Optional[bool] = None


class ScrapeRequest(BaseModel):
    """Request body for the /api/admin/scrape endpoint."""

    source: str = Field(..., description="Name of the source to scrape")


class ScrapeResponse(BaseModel):
    """Response body for scrape operations."""

    source: str
    documents_found: int
    documents_ingested: int
    errors: List[str] = []


class DryRunRequest(BaseModel):
    """Request body for the /api/admin/scrape/dry-run endpoint."""

    source: str


class DryRunResponse(BaseModel):
    """Response for dry-run scrape check."""

    source: str
    reachable: bool
    url: str
    error: Optional[str] = None


class StoreStats(BaseModel):
    """Vector store statistics."""

    total_chunks: int
    total_documents: int
    sources: List[str] = []


class LLMStatus(BaseModel):
    """LLM connectivity status."""

    provider: str
    model: str
    reachable: bool
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
