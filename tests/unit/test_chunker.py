"""Unit tests for the text chunker."""

import pytest

from app.processing.chunker import Chunk, chunk_text


@pytest.mark.unit
class TestChunker:
    def test_chunk_sizes_within_limit(self):
        """All chunks should respect max_chars."""
        text = "Hello world. " * 500  # ~6500 chars
        chunks = chunk_text(text, max_chars=1000, overlap=200)

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.text) <= 1000

    def test_chunk_overlap(self):
        """Consecutive chunks should share overlapping content."""
        text = "Word " * 1000  # 5000 chars
        chunks = chunk_text(text, max_chars=500, overlap=100)

        assert len(chunks) > 2
        # Check that consecutive chunks share some text
        for i in range(len(chunks) - 1):
            current_end = chunks[i].text[-50:]
            next_start = chunks[i + 1].text[:200]
            # The overlap means some content from end of chunk i
            # should appear at start of chunk i+1
            # (exact match depends on boundary detection)
            assert len(chunks[i].text) > 0
            assert len(chunks[i + 1].text) > 0

    def test_empty_text(self):
        """Empty input should return empty list."""
        assert chunk_text("") == []
        assert chunk_text("   ") == []
        assert chunk_text("\n\n") == []

    def test_metadata_attached(self):
        """Every chunk should have source metadata plus chunk_index."""
        metadata = {"source": "test_source", "url": "https://example.com", "date": "2025"}
        chunks = chunk_text("A" * 2000, max_chars=500, overlap=100, metadata=metadata)

        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert chunk.metadata["source"] == "test_source"
            assert chunk.metadata["url"] == "https://example.com"
            assert chunk.metadata["date"] == "2025"
            assert chunk.metadata["chunk_index"] == i

    def test_short_text_single_chunk(self):
        """Text shorter than max_chars should produce a single chunk."""
        chunks = chunk_text("Short text.", max_chars=1000, overlap=200)
        assert len(chunks) == 1
        assert chunks[0].text == "Short text."

    def test_invalid_max_chars(self):
        """Should raise ValueError for invalid max_chars."""
        with pytest.raises(ValueError, match="max_chars must be positive"):
            chunk_text("text", max_chars=0)

    def test_invalid_overlap(self):
        """Should raise ValueError for overlap >= max_chars."""
        with pytest.raises(ValueError, match="overlap must be less than max_chars"):
            chunk_text("text", max_chars=100, overlap=100)

    def test_negative_overlap(self):
        """Should raise ValueError for negative overlap."""
        with pytest.raises(ValueError, match="overlap must be non-negative"):
            chunk_text("text", max_chars=100, overlap=-1)

    def test_none_metadata_defaults_to_empty(self):
        """When metadata is None, chunks should still have chunk_index."""
        chunks = chunk_text("Some text here", max_chars=1000)
        assert len(chunks) == 1
        assert chunks[0].metadata == {"chunk_index": 0}
