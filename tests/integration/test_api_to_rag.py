"""Integration tests for API to RAG pipeline."""

from unittest.mock import MagicMock

import pytest

from app.api.dependencies import get_rag_pipeline
from app.main import app


@pytest.mark.integration
class TestAPIToRAG:
    def test_query_endpoint_returns_structured_response(self, test_client):
        """Test /api/query endpoint returns proper response structure."""
        mock_response = MagicMock()
        mock_response.answer = "Wells Fargo had strong earnings."
        mock_response.citations = [
            MagicMock(
                source_name="wf_earnings",
                source_url="https://example.com/q4.pdf",
                text_snippet="Earnings were strong...",
                date="Q4 2025",
            )
        ]

        mock_pipeline = MagicMock()
        mock_pipeline.query.return_value = mock_response
        app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline
        try:
            response = test_client.post(
                "/api/query",
                json={"question": "What were the earnings?"},
            )
        finally:
            app.dependency_overrides.pop(get_rag_pipeline, None)

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "citations" in data
        assert len(data["citations"]) > 0
        assert data["citations"][0]["source_name"] == "wf_earnings"

    def test_query_with_source_filter(self, test_client):
        """Test /api/query with source filtering."""
        mock_response = MagicMock()
        mock_response.answer = "Annual report info."
        mock_response.citations = []

        mock_pipeline = MagicMock()
        mock_pipeline.query.return_value = mock_response
        app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline
        try:
            response = test_client.post(
                "/api/query",
                json={
                    "question": "Strategic priorities?",
                    "sources": ["wf_annual_reports"],
                },
            )
        finally:
            app.dependency_overrides.pop(get_rag_pipeline, None)

        assert response.status_code == 200

    def test_health_endpoint(self, test_client):
        """Test /health endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_sources_endpoint(self, test_client):
        """Test /api/sources endpoint returns registered sources."""
        response = test_client.get("/api/sources")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        names = [s["name"] for s in data]
        assert "wf_earnings" in names
        assert "wf_annual_reports" in names
