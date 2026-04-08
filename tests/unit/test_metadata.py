"""Unit tests for Pydantic models."""

import pytest

from app.models import (
    CitationResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    SourceInfo,
    StoreStats,
)


@pytest.mark.unit
class TestQueryRequest:
    def test_valid_request(self):
        req = QueryRequest(question="What is revenue?")
        assert req.question == "What is revenue?"
        assert req.sources is None
        assert req.top_k == 10

    def test_with_sources(self):
        req = QueryRequest(question="Revenue?", sources=["wf_earnings"])
        assert req.sources == ["wf_earnings"]

    def test_empty_question_rejected(self):
        with pytest.raises(Exception):
            QueryRequest(question="")

    def test_top_k_bounds(self):
        req = QueryRequest(question="test", top_k=50)
        assert req.top_k == 50

        with pytest.raises(Exception):
            QueryRequest(question="test", top_k=0)

        with pytest.raises(Exception):
            QueryRequest(question="test", top_k=51)


@pytest.mark.unit
class TestQueryResponse:
    def test_basic_response(self):
        resp = QueryResponse(answer="The revenue was $20B.")
        assert resp.answer == "The revenue was $20B."
        assert resp.citations == []

    def test_with_citations(self):
        resp = QueryResponse(
            answer="Answer here",
            citations=[
                CitationResponse(
                    source_name="wf_earnings",
                    source_url="https://example.com/report.pdf",
                    text_snippet="Revenue was...",
                    date="Q4 2025",
                )
            ],
        )
        assert len(resp.citations) == 1
        assert resp.citations[0].source_name == "wf_earnings"


@pytest.mark.unit
class TestSourceInfo:
    def test_source_info(self):
        info = SourceInfo(
            name="wf_earnings",
            display_name="Wells Fargo Quarterly Earnings",
            base_url="https://example.com",
            doc_type="pdf",
        )
        assert info.name == "wf_earnings"


@pytest.mark.unit
class TestStoreStats:
    def test_store_stats(self):
        stats = StoreStats(total_chunks=100, total_documents=5, sources=["wf_earnings"])
        assert stats.total_chunks == 100
        assert stats.total_documents == 5


@pytest.mark.unit
class TestHealthResponse:
    def test_health_response(self):
        health = HealthResponse()
        assert health.status == "ok"
        assert health.timestamp is not None
