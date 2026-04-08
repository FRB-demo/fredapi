"""Component tests for RAG pipeline."""

from unittest.mock import MagicMock, patch

import pytest

from app.rag.pipeline import RAGPipeline, RAGResponse


@pytest.mark.component
class TestRAGPipeline:
    def test_returns_answer_with_citations(self, populated_vector_store, mock_llm):
        """RAG should return an answer with citations when context is available."""
        pipeline = RAGPipeline(
            vector_store=populated_vector_store,
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            api_key="test-key",
        )
        # Replace the LLM client with our mock
        pipeline._client = mock_llm

        result = pipeline.query("What was Wells Fargo's net income?")

        assert isinstance(result, RAGResponse)
        assert len(result.answer) > 0
        assert len(result.citations) > 0
        assert any(c.source_name == "wf_earnings" for c in result.citations)

    def test_empty_retrieval_returns_no_info(self, tmp_chroma_db):
        """When no relevant documents exist, should return 'no information' response."""
        from app.storage.vector_store import VectorStore

        empty_store = VectorStore(persist_directory=tmp_chroma_db)

        pipeline = RAGPipeline(
            vector_store=empty_store,
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            api_key="test-key",
        )

        result = pipeline.query("What is the meaning of life?")

        assert "don't have enough information" in result.answer.lower()
        assert result.citations == []

    def test_source_filtering_in_query(self, populated_vector_store, mock_llm):
        """RAG should respect source filtering."""
        pipeline = RAGPipeline(
            vector_store=populated_vector_store,
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            api_key="test-key",
        )
        pipeline._client = mock_llm

        result = pipeline.query(
            "What are the strategic priorities?",
            sources=["wf_annual_reports"],
        )

        assert isinstance(result, RAGResponse)
        # All citations should be from filtered source
        for citation in result.citations:
            assert citation.source_name == "wf_annual_reports"

    def test_llm_error_handled_gracefully(self, populated_vector_store):
        """LLM errors should be caught and returned as error message."""
        pipeline = RAGPipeline(
            vector_store=populated_vector_store,
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            api_key="test-key",
        )

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        pipeline._client = mock_client

        result = pipeline.query("test question")
        assert "Error" in result.answer
