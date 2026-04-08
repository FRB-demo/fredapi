"""End-to-end tests for the full pipeline."""

from unittest.mock import MagicMock, patch

import pytest
import responses

from app.processing.chunker import chunk_text
from app.processing.pdf_parser import parse_pdf
from app.rag.pipeline import RAGPipeline
from app.scrapers.wf_earnings import WFEarningsScraper
from app.storage.document_store import DocumentStore
from app.storage.vector_store import VectorStore
from app.utils.text import clean_text


@pytest.mark.e2e
class TestFullPipeline:
    def test_scrape_ingest_query_cycle(
        self,
        sample_earnings_pdf,
        tmp_chroma_db,
        tmp_sqlite_db,
        mock_llm,
        mock_html_earnings,
    ):
        """Full scrape → ingest → query cycle."""
        # 1. Simulate scraping (using the sample PDF as the scraped document)
        text = parse_pdf(sample_earnings_pdf)
        text = clean_text(text)

        # 2. Chunk and store
        metadata = {
            "source": "wf_earnings",
            "url": "https://example.com/test-earnings.pdf",
            "title": "Q4 2025 Earnings",
            "date": "Q4 2025",
            "doc_type": "pdf",
        }
        chunks = chunk_text(text, max_chars=500, overlap=100, metadata=metadata)

        vector_store = VectorStore(persist_directory=tmp_chroma_db)
        vector_store.add_chunks(chunks)

        # 3. Record in document store
        doc_store = DocumentStore(db_path=tmp_sqlite_db)
        doc_store.add_document(
            source_name="wf_earnings",
            url="https://example.com/test-earnings.pdf",
            title="Q4 2025 Earnings",
            date="Q4 2025",
            doc_type="pdf",
            chunk_count=len(chunks),
        )

        # 4. Query via RAG
        pipeline = RAGPipeline(
            vector_store=vector_store,
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            api_key="test-key",
        )
        pipeline._client = mock_llm

        result = pipeline.query("What was net income?")

        assert len(result.answer) > 0
        assert len(result.citations) > 0

        # 5. Verify document store
        docs = doc_store.get_documents()
        assert len(docs) == 1
        assert docs[0]["source_name"] == "wf_earnings"

        # 6. Verify stats
        stats = vector_store.get_stats()
        assert stats["total_chunks"] == len(chunks)
