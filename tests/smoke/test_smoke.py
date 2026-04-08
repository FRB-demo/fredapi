"""Smoke tests — quick health checks for the application."""

from unittest.mock import MagicMock, patch

import pytest

from app.api.dependencies import get_document_store, get_rag_pipeline, get_vector_store
from app.main import app


@pytest.mark.smoke
class TestSmoke:
    def test_health_endpoint(self, test_client):
        """Health endpoint should respond with 200 OK."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_vector_store_initializes(self, tmp_chroma_db):
        """Vector store should initialize without errors."""
        from app.storage.vector_store import VectorStore

        store = VectorStore(persist_directory=tmp_chroma_db)
        stats = store.get_stats()
        assert stats["total_chunks"] == 0

    def test_sources_list_not_empty(self, test_client):
        """Sources endpoint should return at least one source."""
        response = test_client.get("/api/sources")
        assert response.status_code == 200
        sources = response.json()
        assert len(sources) >= 1

    def test_query_endpoint_accepts_request(self, test_client):
        """Query endpoint should accept a well-formed request."""
        mock_response = MagicMock()
        mock_response.answer = "Test answer"
        mock_response.citations = []

        mock_pipeline = MagicMock()
        mock_pipeline.query.return_value = mock_response
        app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline
        try:
            response = test_client.post(
                "/api/query",
                json={"question": "test question"},
            )
        finally:
            app.dependency_overrides.pop(get_rag_pipeline, None)

        assert response.status_code == 200

    def test_llm_status_endpoint(self, test_client):
        """LLM status endpoint should respond."""
        mock_pipeline = MagicMock()
        mock_pipeline.check_llm_connection.return_value = (False, "Not configured")
        app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline
        try:
            response = test_client.get("/api/admin/llm/status")
        finally:
            app.dependency_overrides.pop(get_rag_pipeline, None)

        assert response.status_code == 200

    def test_store_stats_endpoint(self, test_client):
        """Store stats endpoint should respond."""
        mock_store = MagicMock()
        mock_store.get_stats.return_value = {"total_chunks": 0, "sources": []}
        mock_doc_store = MagicMock()
        mock_doc_store.get_total_count.return_value = 0

        app.dependency_overrides[get_vector_store] = lambda: mock_store
        app.dependency_overrides[get_document_store] = lambda: mock_doc_store
        try:
            response = test_client.get("/api/admin/store/stats")
        finally:
            app.dependency_overrides.pop(get_vector_store, None)
            app.dependency_overrides.pop(get_document_store, None)

        assert response.status_code == 200

    def test_scraper_dry_run_endpoint(self, test_client):
        """Dry-run endpoint should accept valid source name."""
        with patch("app.api.routes.get_scraper") as mock_get:
            mock_scraper = MagicMock()
            mock_scraper.health_check.return_value = True
            mock_scraper.base_url = "https://example.com"
            mock_scraper.last_error = None
            mock_get.return_value = mock_scraper

            response = test_client.post(
                "/api/admin/scrape/dry-run",
                json={"source": "wf_earnings"},
            )

        assert response.status_code == 200
        assert response.json()["reachable"] is True
