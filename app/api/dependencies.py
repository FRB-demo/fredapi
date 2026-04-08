"""FastAPI dependencies for dependency injection."""

from functools import lru_cache
from typing import Optional

from app.config import get_settings
from app.rag.pipeline import RAGPipeline
from app.storage.document_store import DocumentStore
from app.storage.vector_store import VectorStore

_vector_store: Optional[VectorStore] = None
_document_store: Optional[DocumentStore] = None
_rag_pipeline: Optional[RAGPipeline] = None


def get_vector_store() -> VectorStore:
    """Get or create the VectorStore singleton."""
    global _vector_store
    if _vector_store is None:
        settings = get_settings()
        _vector_store = VectorStore(
            persist_directory=settings.chroma_db_path,
            embedding_model=settings.embedding_model,
        )
    return _vector_store


def get_document_store() -> DocumentStore:
    """Get or create the DocumentStore singleton."""
    global _document_store
    if _document_store is None:
        settings = get_settings()
        _document_store = DocumentStore(db_path=settings.sqlite_db_path)
    return _document_store


def get_rag_pipeline() -> RAGPipeline:
    """Get or create the RAGPipeline singleton."""
    global _rag_pipeline
    if _rag_pipeline is None:
        settings = get_settings()
        _rag_pipeline = RAGPipeline(
            vector_store=get_vector_store(),
            llm_provider=settings.llm_provider,
            llm_model=settings.llm_model,
            llm_base_url=settings.get_llm_base_url(),
            api_key=settings.openai_api_key,
        )
    return _rag_pipeline


def reset_dependencies():
    """Reset all cached dependencies (useful for testing)."""
    global _vector_store, _document_store, _rag_pipeline
    _vector_store = None
    _document_store = None
    _rag_pipeline = None
