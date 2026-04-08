"""RAG pipeline: query → retrieve → LLM → response with citations."""

from dataclasses import dataclass, field
from typing import List, Optional

from openai import OpenAI

from app.storage.vector_store import VectorStore


@dataclass
class Citation:
    """A citation from a source document."""

    source_name: str
    source_url: str
    text_snippet: str
    date: Optional[str] = None


@dataclass
class RAGResponse:
    """Response from the RAG pipeline."""

    answer: str
    citations: List[Citation] = field(default_factory=list)


SYSTEM_PROMPT = """You are a financial research assistant. Answer questions based ONLY on the provided context documents.

Rules:
1. Only use information from the provided context to answer questions.
2. If the context does not contain enough information to answer, say "I don't have enough information in the available documents to answer this question."
3. Cite which source documents you used by referencing the source name and any relevant dates.
4. Be precise and factual. Do not speculate beyond what the documents state.
5. When quoting figures or data, mention the specific document source.
"""

QUERY_TEMPLATE = """Context documents:
{context}

Question: {question}

Please answer the question based only on the context provided above. Cite your sources."""


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline."""

    def __init__(
        self,
        vector_store: VectorStore,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o-mini",
        llm_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize the RAG pipeline.

        Args:
            vector_store: VectorStore instance for retrieval.
            llm_provider: LLM provider ("openai" or "ollama").
            llm_model: Model name to use.
            llm_base_url: Base URL for the LLM API (for Ollama compatibility).
            api_key: API key for the LLM provider.
        """
        self._vector_store = vector_store
        self._llm_model = llm_model
        self._llm_provider = llm_provider

        client_kwargs = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        if llm_base_url:
            client_kwargs["base_url"] = llm_base_url
        elif llm_provider == "ollama":
            client_kwargs["base_url"] = "http://localhost:11434/v1"
            if not api_key:
                client_kwargs["api_key"] = "ollama"

        self._client = OpenAI(**client_kwargs)

    def query(
        self,
        question: str,
        sources: Optional[List[str]] = None,
        top_k: int = 10,
    ) -> RAGResponse:
        """Run the full RAG pipeline.

        1. Retrieve relevant chunks from vector store (with source filtering)
        2. Build prompt with retrieved context
        3. Call LLM
        4. Parse response and extract citations

        Args:
            question: The user's question.
            sources: Optional list of source names to filter retrieval.
            top_k: Number of chunks to retrieve.

        Returns:
            RAGResponse with answer and citations.
        """
        # 1. Retrieve relevant chunks
        chunks = self._vector_store.query(
            query_text=question,
            filter_sources=sources,
            k=top_k,
        )

        if not chunks:
            return RAGResponse(
                answer="I don't have enough information in the available documents to answer this question. No relevant documents were found.",
                citations=[],
            )

        # 2. Build context from chunks
        context_parts = []
        citations = []
        seen_sources = set()

        for i, chunk in enumerate(chunks):
            source = chunk.metadata.get("source", "Unknown")
            url = chunk.metadata.get("url", "")
            date = chunk.metadata.get("date")

            context_parts.append(
                f"[Source {i + 1}: {source}]\n{chunk.text}"
            )

            source_key = (source, url)
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                citations.append(
                    Citation(
                        source_name=source,
                        source_url=url,
                        text_snippet=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                        date=date,
                    )
                )

        context = "\n\n---\n\n".join(context_parts)

        # 3. Call LLM
        user_message = QUERY_TEMPLATE.format(context=context, question=question)

        try:
            response = self._client.chat.completions.create(
                model=self._llm_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=1500,
            )
            answer = response.choices[0].message.content or "No response generated."
        except Exception as e:
            answer = f"Error communicating with LLM: {e}"

        return RAGResponse(answer=answer, citations=citations)

    def check_llm_connection(self) -> tuple[bool, Optional[str]]:
        """Check if the LLM is reachable.

        Returns:
            Tuple of (reachable, error_message).
        """
        try:
            self._client.models.list()
            return True, None
        except Exception as e:
            return False, str(e)
