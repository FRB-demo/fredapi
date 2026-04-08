"""API endpoints for the AI Research Assistant."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_document_store, get_rag_pipeline, get_vector_store
from app.config import get_settings
from app.models import (
    CitationResponse,
    DryRunRequest,
    DryRunResponse,
    HealthResponse,
    LLMStatus,
    QueryRequest,
    QueryResponse,
    ScrapeRequest,
    ScrapeResponse,
    SourceInfo,
    StoreStats,
)
from app.processing.chunker import chunk_text
from app.processing.pdf_parser import PDFParseError, parse_pdf
from app.rag.pipeline import RAGPipeline
from app.scrapers.registry import get_all_sources, get_scraper
from app.storage.document_store import DocumentStore
from app.storage.vector_store import VectorStore
from app.utils.text import clean_text

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


@router.get("/api/sources", response_model=List[SourceInfo])
async def list_sources():
    """List all registered data sources."""
    sources = get_all_sources()
    return [
        SourceInfo(
            name=s["name"],
            display_name=s["display_name"],
            base_url=s["base_url"],
            doc_type=s["doc_type"],
        )
        for s in sources
    ]


@router.post("/api/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline),
):
    """Query documents using RAG pipeline."""
    result = rag.query(
        question=request.question,
        sources=request.sources,
        top_k=request.top_k,
    )

    citations = [
        CitationResponse(
            source_name=c.source_name,
            source_url=c.source_url,
            text_snippet=c.text_snippet,
            date=c.date,
        )
        for c in result.citations
    ]

    return QueryResponse(answer=result.answer, citations=citations)


@router.post("/api/admin/scrape", response_model=ScrapeResponse)
async def scrape_source(
    request: ScrapeRequest,
    vector_store: VectorStore = Depends(get_vector_store),
    doc_store: DocumentStore = Depends(get_document_store),
):
    """Trigger scraping and ingestion for a source."""
    try:
        scraper = get_scraper(request.source)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    errors: List[str] = []

    # Scrape documents
    try:
        documents = scraper.scrape()
    except Exception as e:
        logger.error(f"Scraper {request.source} failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {e}")

    # Ingest each document
    ingested_count = 0
    for doc in documents:
        try:
            # Skip if already ingested
            if doc_store.document_exists(doc.url):
                continue

            # Parse PDF
            if doc.local_path and doc.doc_type == "pdf":
                try:
                    text = parse_pdf(doc.local_path)
                except PDFParseError as e:
                    errors.append(f"Failed to parse {doc.title}: {e}")
                    continue
            elif doc.content:
                text = doc.content
            else:
                errors.append(f"No content for {doc.title}")
                continue

            # Clean and chunk text
            text = clean_text(text)
            metadata = {
                "source": doc.source_name,
                "url": doc.url,
                "title": doc.title,
                "date": doc.date or "",
                "doc_type": doc.doc_type,
            }
            chunks = chunk_text(text, metadata=metadata)

            # Store in vector store
            vector_store.add_chunks(chunks)

            # Record in document store
            doc_store.add_document(
                source_name=doc.source_name,
                url=doc.url,
                title=doc.title,
                date=doc.date,
                doc_type=doc.doc_type,
                local_path=doc.local_path,
                chunk_count=len(chunks),
            )

            ingested_count += 1

        except Exception as e:
            errors.append(f"Error ingesting {doc.title}: {e}")
            logger.error(f"Ingestion error for {doc.title}: {e}")

    return ScrapeResponse(
        source=request.source,
        documents_found=len(documents),
        documents_ingested=ingested_count,
        errors=errors,
    )


@router.get("/api/admin/store/stats", response_model=StoreStats)
async def store_stats(
    vector_store: VectorStore = Depends(get_vector_store),
    doc_store: DocumentStore = Depends(get_document_store),
):
    """Get vector store statistics."""
    stats = vector_store.get_stats()
    total_docs = doc_store.get_total_count()

    return StoreStats(
        total_chunks=stats["total_chunks"],
        total_documents=total_docs,
        sources=stats["sources"],
    )


@router.get("/api/admin/llm/status", response_model=LLMStatus)
async def llm_status(
    rag: RAGPipeline = Depends(get_rag_pipeline),
):
    """Check if the LLM is reachable."""
    settings = get_settings()
    reachable, error = rag.check_llm_connection()

    return LLMStatus(
        provider=settings.llm_provider,
        model=settings.llm_model,
        reachable=reachable,
        error=error,
    )


@router.post("/api/admin/scrape/dry-run", response_model=DryRunResponse)
async def scrape_dry_run(request: DryRunRequest):
    """Check if a source URL is reachable (dry run)."""
    try:
        scraper = get_scraper(request.source)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    reachable = scraper.health_check()

    return DryRunResponse(
        source=request.source,
        reachable=reachable,
        url=scraper.base_url,
        error=scraper.last_error if not reachable else None,
    )
