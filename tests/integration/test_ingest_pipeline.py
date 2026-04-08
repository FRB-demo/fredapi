"""Integration tests for the ingest pipeline."""

import os

import pytest

from app.processing.chunker import chunk_text
from app.processing.pdf_parser import parse_pdf
from app.storage.vector_store import VectorStore
from app.utils.text import clean_text


@pytest.mark.integration
class TestIngestPipeline:
    def test_pdf_to_store_pipeline(self, sample_earnings_pdf, tmp_chroma_db):
        """Test full PDF → parse → chunk → embed → store → retrieve pipeline."""
        # 1. Parse PDF
        text = parse_pdf(sample_earnings_pdf)
        assert len(text) > 0

        # 2. Clean text
        text = clean_text(text)
        assert len(text) > 0

        # 3. Chunk text
        metadata = {
            "source": "wf_earnings",
            "url": "https://example.com/test.pdf",
            "title": "Test Earnings Report",
            "date": "Q4 2025",
            "doc_type": "pdf",
        }
        chunks = chunk_text(text, max_chars=500, overlap=100, metadata=metadata)
        assert len(chunks) > 0

        # 4. Store in vector store
        store = VectorStore(persist_directory=tmp_chroma_db)
        added = store.add_chunks(chunks)
        assert added == len(chunks)

        # 5. Verify retrieval
        results = store.query("Wells Fargo earnings")
        assert len(results) > 0
        assert all(r.metadata.get("source") == "wf_earnings" for r in results)

        # 6. Verify stats
        stats = store.get_stats()
        assert stats["total_chunks"] == len(chunks)
        assert "wf_earnings" in stats["sources"]
