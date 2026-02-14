#!/usr/bin/env python3
"""
Embed ALL schemes from backend/data_f/all_schemes.json into ChromaDB.
No quality filter – every scheme in the JSON is embedded so nothing is missing.

Run from backend directory:
  python embed_all_schemes.py

Or from project root:
  cd backend && python embed_all_schemes.py

First run: downloads the sentence-transformers model (~80MB) and embeds all schemes (~5–10 min).
Subsequent runs: deletes existing ChromaDB and re-embeds everything from the JSON.
"""

import json
import os
import shutil
import sys
from pathlib import Path

# Ensure backend is on path when run as script
BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Now app imports will work
from app.config import settings
from app.utils.data_loader import load_schemes_json, prepare_scheme_text_for_embedding

CHROMA_PATH = str(settings.get_chroma_path(BACKEND_ROOT))
SCHEMES_PATH = settings.get_schemes_path(BACKEND_ROOT)
COLLECTION_NAME = "government_schemes"
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 256


def load_all_schemes_no_filter() -> list:
    """Load every scheme from all_schemes.json with NO quality or other filter."""
    if not SCHEMES_PATH.exists():
        raise FileNotFoundError(f"Schemes file not found: {SCHEMES_PATH}")
    data = load_schemes_json(SCHEMES_PATH)
    schemes = data.get("schemes", [])
    if not isinstance(schemes, list):
        return []
    return schemes


def main():
    print(f"Schemes JSON: {SCHEMES_PATH}")
    print(f"ChromaDB path: {CHROMA_PATH}")
    print()

    # 1. Load ALL schemes (no filter)
    print("Loading ALL schemes from JSON (no quality filter)...")
    schemes = load_all_schemes_no_filter()
    total = len(schemes)
    if total == 0:
        print("ERROR: No schemes found in JSON.")
        sys.exit(1)
    print(f"Loaded {total} schemes from {SCHEMES_PATH.name}")
    print()

    # 2. Load model
    print(f"Loading sentence-transformers model: {MODEL_NAME}...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded.")
    print()

    # 3. Remove existing ChromaDB so we rebuild from scratch
    if os.path.isdir(CHROMA_PATH):
        print(f"Removing existing ChromaDB at {CHROMA_PATH}...")
        shutil.rmtree(CHROMA_PATH)
        print("Removed.")
    os.makedirs(CHROMA_PATH, exist_ok=True)
    print()

    # 4. Create ChromaDB client and collection (no embedding function – we provide embeddings)
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    print(f"ChromaDB collection '{COLLECTION_NAME}' ready.")
    print()

    # 5. Embed every scheme in batches
    print(f"Embedding all {total} schemes (batch size {BATCH_SIZE})...")
    added = 0
    skipped_no_id = 0

    for i in range(0, total, BATCH_SIZE):
        batch = schemes[i : i + BATCH_SIZE]
        ids = []
        texts = []
        metadatas = []

        for j, scheme in enumerate(batch):
            idx = i + j
            # Use scheme_id if present, else unique fallback so we never skip
            scheme_id = scheme.get("scheme_id") or ""
            if not scheme_id:
                scheme_id = f"scheme-{idx}"
                skipped_no_id += 1

            text = prepare_scheme_text_for_embedding(scheme)
            text = (text[:8000] if text else "")

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

        embeddings = model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        embeddings_list = embeddings.tolist()

        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings_list,
            metadatas=metadatas,
        )
        added += len(ids)
        pct = 100.0 * added / total
        print(f"  Embedded {added}/{total} ({pct:.1f}%)")
    print()

    if skipped_no_id:
        print(f"Note: {skipped_no_id} schemes had no scheme_id; used fallback ids (scheme-0, scheme-1, ...).")
    print()

    # 6. Verify
    final_count = collection.count()
    if final_count != total:
        print(f"WARNING: ChromaDB count ({final_count}) != JSON scheme count ({total}).")
        sys.exit(1)
    print(f"ChromaDB initialized with {final_count} schemes. Nothing missing.")
    print(f"Saved to: {CHROMA_PATH}")
    print()
    print("Done. You can start the backend; it will load this ChromaDB from disk.")


if __name__ == "__main__":
    main()
