"""
build_vectordb.py - Convert all_schemes.json to vectors and store in ChromaDB.

Uses OpenAI text-embedding-3-large for embeddings (see app.utils.embedding_function).

Reads:  backend/data_f/all_schemes.json
Writes: backend/chroma_db/  (ChromaDB persistent storage)

Usage:
    cd backend
    set OPENAI_API_KEY=sk-...
    python build_vectordb.py
"""

import json
import logging
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure backend is on path when run as script
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

# ============================================================
# Config
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent
SCHEMES_PATH = BACKEND_DIR / "data_f" / "all_schemes.json"
CHROMA_DIR = BACKEND_DIR / "chroma_db"
COLLECTION_NAME = "government_schemes"
# Keep batches small to stay under OpenAI TPM (e.g. 40k tokens/min for text-embedding-3-large)
BATCH_SIZE = 20
BATCH_DELAY_SEC = 16  # Delay between batches to respect rate limit (TPM)
MIN_QUALITY_SCORE = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================
# 1. Load schemes from JSON
# ============================================================

def load_schemes() -> List[Dict[str, Any]]:
    """Load schemes from all_schemes.json."""
    if not SCHEMES_PATH.exists():
        logger.error("File not found: %s", SCHEMES_PATH)
        sys.exit(1)

    logger.info("Reading %s ...", SCHEMES_PATH)
    with SCHEMES_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    # Handle both formats: {"schemes": [...]} or bare list [...]
    if isinstance(data, dict):
        schemes = data.get("schemes", [])
    elif isinstance(data, list):
        schemes = data
    else:
        schemes = []

    logger.info("Found %d total schemes in file", len(schemes))

    # Filter low quality
    valid = [s for s in schemes if isinstance(s, dict) and s.get("data_quality_score", 0) >= MIN_QUALITY_SCORE]
    filtered = len(schemes) - len(valid)
    if filtered:
        logger.info("Filtered out %d schemes with quality < %d", filtered, MIN_QUALITY_SCORE)

    logger.info("Schemes to index: %d", len(valid))
    return valid


# ============================================================
# 2. Prepare text for embedding
# ============================================================

def prepare_text(scheme: Dict[str, Any]) -> str:
    """Build a rich text string from scheme fields for vector embedding."""
    parts = []

    name = scheme.get("scheme_name", "")
    if name:
        parts.append(f"Scheme: {name}")

    category = scheme.get("category", "")
    if category:
        parts.append(f"Category: {category}")

    brief = scheme.get("brief_description", "")
    if brief and len(brief) > 20:
        parts.append(f"Description: {brief}")

    detailed = scheme.get("detailed_description", "")
    if detailed and len(detailed) > len(brief):
        parts.append(f"Details: {detailed}")

    benefits = scheme.get("benefits", {})
    if isinstance(benefits, dict):
        summary = benefits.get("summary", "")
        if summary:
            parts.append(f"Benefits: {summary}")
        financial = benefits.get("financial_benefit", "")
        if financial:
            parts.append(f"Financial Benefit: {financial}")

    elig = scheme.get("eligibility_criteria", {})
    if isinstance(elig, dict):
        raw = elig.get("raw_eligibility_text", "")
        if raw and raw not in ("Check Eligibility", "Eligibility criteria not clearly specified"):
            parts.append(f"Eligibility: {raw}")
        for field in ["occupation", "state", "caste_category", "income_limit", "age_range"]:
            val = elig.get(field, "")
            if val and val not in ("any", "unknown", ""):
                parts.append(f"{field.replace('_', ' ').title()}: {val}")

    target = scheme.get("target_beneficiaries", "")
    if target:
        parts.append(f"For: {target}")

    ministry = scheme.get("ministry_department", "")
    if ministry:
        parts.append(f"Ministry: {ministry}")

    return " | ".join(filter(None, parts))


# ============================================================
# 3. Build ChromaDB
# ============================================================

def build_vectordb(schemes: List[Dict[str, Any]], fresh: bool = True) -> None:
    """Index all schemes into ChromaDB using OpenAI text-embedding-3-large."""
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
    except ImportError:
        logger.error("chromadb not installed. Run: pip install chromadb")
        sys.exit(1)

    from app.utils.embedding_function import get_embedding_function

    embedding_function = get_embedding_function()

    # Optionally wipe old DB for a clean build
    if fresh and CHROMA_DIR.exists():
        logger.info("Removing old vector DB at %s ...", CHROMA_DIR)
        shutil.rmtree(CHROMA_DIR)

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    from app.config import settings
    logger.info("Initializing ChromaDB at %s (OpenAI %s) ...", CHROMA_DIR, settings.OPENAI_EMBEDDING_MODEL)
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    # Delete collection if it already exists (clean slate)
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info("Deleted existing collection '%s'", COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Indian government schemes for Scheme Saathi"},
        embedding_function=embedding_function,
    )

    # Prepare data
    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    skipped = 0

    for s in schemes:
        sid = s.get("scheme_id", "")
        if not sid:
            skipped += 1
            continue

        # Avoid duplicate IDs
        if sid in ids:
            skipped += 1
            continue

        text = prepare_text(s)
        if not text or len(text) < 20:
            skipped += 1
            continue

        ids.append(sid)
        documents.append(text[:8000])  # ChromaDB document length limit

        elig = s.get("eligibility_criteria") or {}
        if not isinstance(elig, dict):
            elig = {}

        metadatas.append({
            "scheme_name": (s.get("scheme_name") or "")[:200],
            "category": (s.get("category") or "")[:200],
            "state": (elig.get("state") or "All India")[:200],
            "occupation": (elig.get("occupation") or "any")[:200],
            "quality_score": int(s.get("data_quality_score", 0)),
        })

    if skipped:
        logger.info("Skipped %d schemes (no ID, duplicate, or empty text)", skipped)

    logger.info("Indexing %d schemes into ChromaDB ...", len(ids))

    # Add in batches
    total_batches = (len(ids) + BATCH_SIZE - 1) // BATCH_SIZE
    start_time = time.time()

    for i in range(0, len(ids), BATCH_SIZE):
        batch_num = (i // BATCH_SIZE) + 1
        batch_ids = ids[i : i + BATCH_SIZE]
        batch_docs = documents[i : i + BATCH_SIZE]
        batch_meta = metadatas[i : i + BATCH_SIZE]

        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_meta,
        )

        elapsed = time.time() - start_time
        logger.info(
            "  Batch %d/%d done  (%d schemes so far, %.1fs elapsed)",
            batch_num, total_batches, min(i + BATCH_SIZE, len(ids)), elapsed,
        )

        # Throttle to stay under OpenAI TPM (tokens per minute) limit
        if i + BATCH_SIZE < len(ids) and BATCH_DELAY_SEC > 0:
            time.sleep(BATCH_DELAY_SEC)

    elapsed = time.time() - start_time
    final_count = collection.count()

    logger.info("")
    logger.info("=" * 50)
    logger.info("  VECTOR DB BUILD COMPLETE")
    logger.info("=" * 50)
    logger.info("  Schemes indexed : %d", final_count)
    logger.info("  Time taken      : %.1f seconds", elapsed)
    logger.info("  DB location     : %s", CHROMA_DIR)
    logger.info("=" * 50)


# ============================================================
# 4. Quick test
# ============================================================

def test_search(query: str = "farmer pension scheme") -> None:
    """Run a quick test search to verify the DB works."""
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    from app.utils.embedding_function import get_embedding_function

    logger.info("\nTest search: '%s'", query)
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    embedding_function = get_embedding_function()
    collection = client.get_collection(COLLECTION_NAME, embedding_function=embedding_function)

    results = collection.query(
        query_texts=[query],
        n_results=5,
        include=["metadatas", "distances"],
    )

    print(f"\nTop 5 results for: '{query}'")
    print("-" * 60)
    for i, (sid, meta, dist) in enumerate(
        zip(results["ids"][0], results["metadatas"][0], results["distances"][0]), 1
    ):
        score = max(0, 1 - (dist / 2))
        print(f"  {i}. [{score:.2f}] {meta['scheme_name']}")
        print(f"     Category: {meta['category']} | State: {meta['state']}")
    print("-" * 60)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  Scheme Saathi - Vector DB Builder")
    print("=" * 50)
    print()

    # Step 1: Load
    schemes = load_schemes()
    if not schemes:
        print("[FAIL] No schemes to index.")
        sys.exit(1)

    # Step 2: Build
    build_vectordb(schemes, fresh=True)

    # Step 3: Quick test
    test_search("scholarship for SC ST students")
    test_search("health insurance for poor family")
    test_search("loan for small business women entrepreneur")

    print("\n[DONE] Vector DB is ready. Start the backend server:")
    print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
