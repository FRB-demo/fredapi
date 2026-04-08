"""Embedding generation using sentence-transformers."""

from typing import List, Optional

_model_instance = None
_model_name: Optional[str] = None


def _get_model(model_name: str = "all-MiniLM-L6-v2"):
    """Lazy-load singleton SentenceTransformer model."""
    global _model_instance, _model_name

    if _model_instance is None or _model_name != model_name:
        from sentence_transformers import SentenceTransformer

        _model_instance = SentenceTransformer(model_name)
        _model_name = model_name

    return _model_instance


def embed_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> List[List[float]]:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.
        model_name: Name of the sentence-transformers model to use.

    Returns:
        List of embedding vectors (each a list of floats).
    """
    if not texts:
        return []

    model = _get_model(model_name)
    embeddings = model.encode(texts, show_progress_bar=False)
    return [emb.tolist() for emb in embeddings]
