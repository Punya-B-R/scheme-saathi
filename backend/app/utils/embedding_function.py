"""
Shared embedding function for ChromaDB.
Uses OpenAI text-embedding-3-large so build_vectordb and RAG service stay in sync.
"""

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def get_embedding_function() -> Any:
    """
    Return ChromaDB embedding function for OpenAI text-embedding-3-large.
    Used by build_vectordb.py and rag_service.py so add and query use the same model.
    """
    api_key = (settings.OPENAI_API_KEY or "").strip()
    if not api_key or api_key == "placeholder":
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to .env for OpenAI embeddings (text-embedding-3-large)."
        )

    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    ef = OpenAIEmbeddingFunction(
        model_name=settings.OPENAI_EMBEDDING_MODEL,
        api_key=api_key,
    )
    logger.info("Using OpenAI embedding model: %s", settings.OPENAI_EMBEDDING_MODEL)
    return ef
