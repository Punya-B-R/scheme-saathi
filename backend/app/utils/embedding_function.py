"""
Shared embedding function for ChromaDB.
Uses OpenAI embedding models so build_vectordb and RAG service stay in sync.
"""

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# OpenAI embedding model IDs that are valid for the embeddings API (not chat models).
VALID_EMBEDDING_MODELS = (
    "text-embedding-3-large",
    "text-embedding-3-small",
    "text-embedding-ada-002",
)
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def _resolve_embedding_model() -> str:
    """Return a valid embedding model ID; fall back to default if .env has an invalid one."""
    raw = (settings.OPENAI_EMBEDDING_MODEL or "").strip()
    if raw in VALID_EMBEDDING_MODELS:
        return raw
    if raw:
        logger.warning(
            "OPENAI_EMBEDDING_MODEL=%r is not a valid embedding model (e.g. chat models like gpt-4 are invalid). Using %s. If your ChromaDB was built with another model, run: python build_vectordb.py",
            raw,
            DEFAULT_EMBEDDING_MODEL,
        )
    return DEFAULT_EMBEDDING_MODEL


def get_embedding_function() -> Any:
    """
    Return ChromaDB embedding function for OpenAI.
    Used by build_vectordb.py and rag_service.py so add and query use the same model.
    """
    api_key = (settings.OPENAI_API_KEY or "").strip()
    if not api_key or api_key == "placeholder":
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to .env for OpenAI embeddings."
        )

    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    model = _resolve_embedding_model()
    ef = OpenAIEmbeddingFunction(
        model_name=model,
        api_key=api_key,
    )
    logger.info("Using OpenAI embedding model: %s", model)
    return ef
