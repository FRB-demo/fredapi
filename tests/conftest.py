"""Shared pytest fixtures."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_dir():
    """Create a temporary directory that is cleaned up after the test."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def tmp_chroma_db(tmp_dir):
    """Temporary ChromaDB directory."""
    chroma_path = os.path.join(tmp_dir, "chroma_db")
    os.makedirs(chroma_path, exist_ok=True)
    return chroma_path


@pytest.fixture
def tmp_sqlite_db(tmp_dir):
    """Temporary SQLite database path."""
    return os.path.join(tmp_dir, "metadata.db")


@pytest.fixture
def sample_earnings_pdf():
    """Path to a sample earnings PDF fixture.

    Creates a simple PDF with known content if it doesn't exist.
    """
    pdf_path = FIXTURES_DIR / "pdfs" / "sample_earnings.pdf"
    if not pdf_path.exists():
        _create_sample_pdf(pdf_path)
    return str(pdf_path)


@pytest.fixture
def corrupted_pdf(tmp_dir):
    """Path to a corrupted PDF file."""
    path = os.path.join(tmp_dir, "corrupted.pdf")
    with open(path, "wb") as f:
        f.write(b"This is not a valid PDF file content at all.")
    return path


@pytest.fixture
def golden_qa():
    """Load golden Q&A pairs for regression testing."""
    qa_path = FIXTURES_DIR / "golden_qa.json"
    with open(qa_path) as f:
        return json.load(f)


@pytest.fixture
def mock_html_earnings():
    """Load mocked Wells Fargo earnings HTML."""
    html_path = FIXTURES_DIR / "html" / "wf_earnings_page.html"
    with open(html_path) as f:
        return f.read()


@pytest.fixture
def mock_llm():
    """Mock LLM that returns predictable responses."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="Based on the provided documents, Wells Fargo reported net income of $5.1 billion in Q4 2025. [Source: wf_earnings]"
            )
        )
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_client.models.list.return_value = MagicMock()

    return mock_client


@pytest.fixture
def populated_vector_store(tmp_chroma_db):
    """A vector store pre-populated with sample chunks."""
    from app.processing.chunker import Chunk
    from app.storage.vector_store import VectorStore

    store = VectorStore(persist_directory=tmp_chroma_db)

    chunks = [
        Chunk(
            text="Wells Fargo reported net income of $5.1 billion in Q4 2025, driven by strong consumer banking performance.",
            metadata={
                "source": "wf_earnings",
                "url": "https://example.com/q4-2025.pdf",
                "title": "Q4 2025 Earnings",
                "date": "Q4 2025",
                "doc_type": "pdf",
                "chunk_index": 0,
            },
        ),
        Chunk(
            text="Total revenue for the quarter was $20.5 billion, representing a 3% increase year-over-year.",
            metadata={
                "source": "wf_earnings",
                "url": "https://example.com/q4-2025.pdf",
                "title": "Q4 2025 Earnings",
                "date": "Q4 2025",
                "doc_type": "pdf",
                "chunk_index": 1,
            },
        ),
        Chunk(
            text="Wells Fargo's 2024 Annual Report highlights key strategic priorities including digital transformation and risk management.",
            metadata={
                "source": "wf_annual_reports",
                "url": "https://example.com/annual-2024.pdf",
                "title": "2024 Annual Report",
                "date": "2024",
                "doc_type": "pdf",
                "chunk_index": 0,
            },
        ),
    ]

    store.add_chunks(chunks)
    return store


@pytest.fixture
def test_client():
    """FastAPI TestClient with mocked dependencies."""
    from app.api import dependencies
    from app.main import app

    # Reset dependencies so tests get fresh instances
    dependencies.reset_dependencies()

    with TestClient(app) as client:
        yield client

    dependencies.reset_dependencies()


def _create_sample_pdf(path: Path):
    """Create a simple PDF with known test content using reportlab."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(path), pagesize=letter)
        c.setFont("Helvetica", 12)

        lines = [
            "Wells Fargo Quarterly Earnings Report - Q4 2025",
            "",
            "Financial Highlights:",
            "Wells Fargo reported net income of $5.1 billion in Q4 2025.",
            "Total revenue was $20.5 billion for the quarter.",
            "Earnings per share were $1.42, exceeding analyst expectations.",
            "",
            "Consumer Banking:",
            "Consumer banking revenue grew 5% year-over-year.",
            "Digital active customers reached 35 million.",
            "",
            "Risk Management:",
            "Credit quality remained stable with net charge-offs of 0.5%.",
            "The provision for credit losses was $1.3 billion.",
        ]

        y = 750
        for line in lines:
            c.drawString(72, y, line)
            y -= 20

        c.save()
    except ImportError:
        # Fallback: create a minimal valid PDF manually
        import struct

        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 183 >>
stream
BT
/F1 12 Tf
72 750 Td
(Wells Fargo Quarterly Earnings Report - Q4 2025) Tj
0 -20 Td
(Wells Fargo reported net income of $5.1 billion in Q4 2025.) Tj
0 -20 Td
(Total revenue was $20.5 billion.) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000501 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
574
%%EOF"""
        with open(path, "wb") as f:
            f.write(pdf_content)
