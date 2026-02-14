"""
Run this ONCE locally to generate ChromaDB embeddings with OpenAI.
Never runs on Render - only on your local machine.

Uses OpenAI text-embedding-3-large (same as rag_service query) so dimensions match.
Requires OPENAI_API_KEY in .env.

Usage: cd backend && python scripts/precompute_embeddings.py
"""

import logging
import os
import shutil
import sys
import time
from pathlib import Path

# Ensure backend is on path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI

from app.config import settings
from app.utils.data_loader import (
    load_schemes_from_json,
    prepare_scheme_text_for_embedding,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHROMA_PATH = str(settings.get_chroma_path(BACKEND_DIR))
COLLECTION_NAME = "government_schemes"
BATCH_SIZE = 20
BATCH_DELAY_SEC = 16


def main() -> None:
    api_key = (settings.OPENAI_API_KEY or "").strip()
    if not api_key or api_key == "placeholder":
        logger.error("OPENAI_API_KEY not set. Add it to .env and run again.")
        sys.exit(1)

    schemes_path = settings.get_schemes_path(BACKEND_DIR)
    schemes = load_schemes_from_json(str(schemes_path))
    logger.info("Loaded %d schemes", len(schemes))

    if not schemes:
        logger.error("No schemes found. Check data_f/all_schemes.json")
        sys.exit(1)

    # Delete existing ChromaDB and recreate
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
        logger.info("Deleted old ChromaDB at %s", CHROMA_PATH)

    os.makedirs(CHROMA_PATH, exist_ok=True)
    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    openai_client = OpenAI(api_key=api_key)
    total = len(schemes)
    added = 0

    for i in range(0, total, BATCH_SIZE):
        batch = schemes[i : i + BATCH_SIZE]
        ids, texts, metadatas = [], [], []

        for scheme in batch:
            scheme_id = scheme.get("scheme_id") or ""
            if not scheme_id:
                continue

            text = prepare_scheme_text_for_embedding(scheme)
            text = (text[:8000] if text else "").strip()
            if not text or len(text) < 20:
                continue

            eligibility = scheme.get("eligibility_criteria") or {}
            if not isinstance(eligibility, dict):
                eligibility = {}
            state = eligibility.get("state") or "All India"
            if isinstance(state, list):
                state = ", ".join(str(s) for s in state)

            ids.append(str(scheme_id))
            texts.append(text)
            metadatas.append({
                "scheme_name": str(scheme.get("scheme_name", ""))[:200],
                "category": str(scheme.get("category", ""))[:200],
                "state": str(state or "All India")[:200],
                "occupation": str(eligibility.get("occupation", "any") or "any")[:200],
            })

        if not ids:
            continue

        try:
            response = openai_client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=texts,
            )
            embeddings = [d.embedding for d in response.data]
            # Ensure order matches (API may return in different order for some models)
            if len(embeddings) != len(ids):
                logger.warning("Embedding count mismatch, skipping batch")
                continue

            collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            added += len(ids)
            pct = 100.0 * added / total
            logger.info("Progress: %d/%d (%.1f%%)", added, total, pct)
        except Exception as e:
            logger.error("OpenAI batch failed: %s", e)
            raise

        if i + BATCH_SIZE < total and BATCH_DELAY_SEC > 0:
            time.sleep(BATCH_DELAY_SEC)

    logger.info("Done! ChromaDB saved at: %s", CHROMA_PATH)
    logger.info("Total schemes embedded: %d", added)
    logger.info("Collection count: %d", collection.count())


if __name__ == "__main__":
    main()
