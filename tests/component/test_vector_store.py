"""Component tests for vector store."""

import pytest

from app.processing.chunker import Chunk
from app.storage.vector_store import VectorStore


@pytest.mark.component
class TestVectorStore:
    def test_store_and_retrieve(self, tmp_chroma_db):
        """Should store chunks and retrieve them by query."""
        store = VectorStore(persist_directory=tmp_chroma_db)

        chunks = [
            Chunk(
                text="Wells Fargo reported strong earnings in Q4.",
                metadata={"source": "wf_earnings", "url": "https://example.com/q4.pdf"},
            ),
            Chunk(
                text="The Federal Reserve raised interest rates.",
                metadata={"source": "fed_reports", "url": "https://example.com/fed.pdf"},
            ),
        ]

        added = store.add_chunks(chunks)
        assert added == 2

        results = store.query("Wells Fargo earnings")
        assert len(results) > 0
        assert any("Wells Fargo" in r.text for r in results)

    def test_source_filtering_excludes_other_sources(self, tmp_chroma_db):
        """Query with source filter should only return matching sources."""
        store = VectorStore(persist_directory=tmp_chroma_db)

        chunks = [
            Chunk(
                text="Wells Fargo Q4 earnings were strong.",
                metadata={"source": "wf_earnings"},
            ),
            Chunk(
                text="Annual report discusses strategy.",
                metadata={"source": "wf_annual_reports"},
            ),
        ]

        store.add_chunks(chunks)

        results = store.query(
            "earnings strategy",
            filter_sources=["wf_earnings"],
        )

        for r in results:
            assert r.metadata.get("source") == "wf_earnings"

    def test_empty_query_returns_results(self, populated_vector_store):
        """Even a vague query should return some results from a populated store."""
        results = populated_vector_store.query("financial information")
        assert len(results) > 0

    def test_stats_reporting(self, populated_vector_store):
        """Stats should report correct chunk count and sources."""
        stats = populated_vector_store.get_stats()
        assert stats["total_chunks"] == 3
        assert "wf_earnings" in stats["sources"]
        assert "wf_annual_reports" in stats["sources"]

    def test_delete_source(self, tmp_chroma_db):
        """Should delete all chunks for a given source."""
        store = VectorStore(persist_directory=tmp_chroma_db)

        chunks = [
            Chunk(text="Chunk from source A", metadata={"source": "source_a"}),
            Chunk(text="Chunk from source B", metadata={"source": "source_b"}),
        ]
        store.add_chunks(chunks)

        deleted = store.delete_source("source_a")
        assert deleted == 1

        stats = store.get_stats()
        assert stats["total_chunks"] == 1
        assert "source_a" not in stats["sources"]

    def test_add_empty_chunks(self, tmp_chroma_db):
        """Adding empty list should return 0."""
        store = VectorStore(persist_directory=tmp_chroma_db)
        assert store.add_chunks([]) == 0
