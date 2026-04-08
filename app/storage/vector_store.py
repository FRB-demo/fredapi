"""ChromaDB wrapper with source filtering."""

import uuid
from typing import Dict, List, Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.processing.chunker import Chunk


class VectorStore:
    """Wrapper around ChromaDB for storing and querying document chunks."""

    def __init__(self, persist_directory: str, embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize ChromaDB with persistent storage.

        Args:
            persist_directory: Path to ChromaDB storage directory.
            embedding_model: Name of the sentence-transformers model for embeddings.
        """
        self._client = chromadb.PersistentClient(path=persist_directory)
        self._embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        self._collection = self._client.get_or_create_collection(
            name="documents",
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: List[Chunk]) -> int:
        """Embed and store chunks with metadata.

        Args:
            chunks: List of Chunk objects to store.

        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0

        ids = [str(uuid.uuid4()) for _ in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        self._collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        return len(chunks)

    def query(
        self,
        query_text: str,
        filter_sources: Optional[List[str]] = None,
        k: int = 10,
    ) -> List[Chunk]:
        """Semantic search with optional source filtering.

        Args:
            query_text: The search query.
            filter_sources: Optional list of source names to filter by.
            k: Number of results to return.

        Returns:
            List of matching Chunk objects, ordered by relevance.
        """
        where_filter = None
        if filter_sources:
            if len(filter_sources) == 1:
                where_filter = {"source": filter_sources[0]}
            else:
                where_filter = {"source": {"$in": filter_sources}}

        try:
            results = self._collection.query(
                query_texts=[query_text],
                n_results=k,
                where=where_filter,
            )
        except Exception:
            # If filter returns no results or other error, return empty
            return []

        chunks = []
        if results and results["documents"] and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                chunks.append(Chunk(text=doc, metadata=meta or {}))

        return chunks

    def get_stats(self) -> Dict:
        """Return statistics about the vector store.

        Returns:
            Dict with total_chunks, sources list, etc.
        """
        count = self._collection.count()

        # Get unique sources from metadata
        sources = set()
        if count > 0:
            # Sample metadata to find sources
            results = self._collection.get(limit=min(count, 10000), include=["metadatas"])
            if results and results["metadatas"]:
                for meta in results["metadatas"]:
                    if meta and "source" in meta:
                        sources.add(meta["source"])

        return {
            "total_chunks": count,
            "sources": sorted(sources),
        }

    def delete_source(self, source_name: str) -> int:
        """Remove all chunks for a given source.

        Args:
            source_name: The source name to delete.

        Returns:
            Number of chunks deleted.
        """
        # Get IDs of chunks with this source
        results = self._collection.get(
            where={"source": source_name},
            include=[],
        )

        if not results or not results["ids"]:
            return 0

        ids_to_delete = results["ids"]
        self._collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)
