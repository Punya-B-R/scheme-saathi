#!/usr/bin/env python3
"""
Check if RAG (ChromaDB + semantic search) is working for Scheme Saathi.
Run from backend directory: python check_rag.py

Exits 0 if all checks pass, 1 otherwise. Loads .env automatically.
"""

import sys
from pathlib import Path

# Ensure backend root is on path and load .env
BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(BACKEND_ROOT / ".env")
except ImportError:
    pass  # .env optional if env vars set

OK = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def main() -> int:
    print("=" * 60)
    print("RAG CHECK – Scheme Saathi")
    print("=" * 60)
    errors = 0

    # 1. Import RAG service (this loads JSON + ChromaDB + embedding)
    print("\n1. Loading RAG service...")
    try:
        from app.services.rag_service import rag_service
        print(f"   {OK} RAG service imported")
    except Exception as e:
        print(f"   {FAIL} Import failed: {e}")
        return 1

    # 2. Schemes loaded from JSON
    total = rag_service.get_total_schemes()
    if total == 0:
        print(f"   {FAIL} No schemes loaded from JSON (check data_f/all_schemes.json)")
        errors += 1
    else:
        print(f"   {OK} Schemes loaded: {total}")

    # 3. ChromaDB health
    print("\n2. ChromaDB health...")
    try:
        healthy = rag_service.check_health()
        if not healthy:
            print(f"   {FAIL} check_health() returned False")
            errors += 1
        else:
            count = rag_service._collection.count() if rag_service._collection else 0
            print(f"   {OK} Collection healthy, count = {count}")
    except Exception as e:
        print(f"   {FAIL} Health check failed: {e}")
        errors += 1

    if errors:
        print("\n" + "=" * 60)
        print("RAG CHECK FAILED – fix above before running search.")
        print("=" * 60)
        return 1

    # 4. Search returns results
    print("\n3. Search (query: 'farmer scholarship')...")
    try:
        results = rag_service.search_schemes("farmer scholarship", user_context=None, top_k=10)
        n = len(results)
        if n == 0:
            print(f"   {FAIL} Search returned 0 results (cards will not show)")
            print("   Possible causes: ChromaDB built with different data, or similarity threshold too high")
            errors += 1
        else:
            print(f"   {OK} Search returned {n} schemes")
    except Exception as e:
        print(f"   {FAIL} Search failed: {e}")
        errors += 1
        results = []

    # 5. Result shape and URL fields (needed for clickable links / cards)
    if results:
        print("\n4. Result shape (scheme_id, name, source_url, official_website)...")
        sample = results[0]
        sid = sample.get("scheme_id")
        name = sample.get("scheme_name", "")[:40]
        src = sample.get("source_url") or ""
        web = sample.get("official_website") or ""

        if not sid:
            print(f"   {WARN} First result has no scheme_id")
        else:
            print(f"   {OK} scheme_id = {sid}")

        print(f"   {OK} scheme_name = {name}...")
        if not src and not web:
            print(f"   {WARN} No source_url or official_website (links may not show)")
        else:
            print(f"   {OK} source_url / official_website present")

        # Count how many have URLs
        with_url = sum(1 for s in results if (s.get("source_url") or s.get("official_website")))
        print(f"   Schemes with URL in this result set: {with_url}/{len(results)}")

    # 6. Second query (no user context) – simulates "not ready" chat path
    print("\n5. Search with no context (simulates first user message)...")
    try:
        results2 = rag_service.search_schemes("I need a scholarship", user_context=None, top_k=5)
        if len(results2) == 0:
            print(f"   {WARN} No results for generic query (cards may not show until user gives more context)")
        else:
            print(f"   {OK} Returned {len(results2)} schemes")
    except Exception as e:
        print(f"   {FAIL} {e}")
        errors += 1

    # Summary
    print("\n" + "=" * 60)
    if errors:
        print("RAG CHECK FAILED")
        print("Fix the [FAIL] items above. Common fixes:")
        print("  - No schemes: ensure data_f/all_schemes.json exists and has 'schemes' array")
        print("  - Search returns 0: run 'python build_vectordb.py' to (re)build ChromaDB")
        print("  - Import/embedding error: set OPENAI_API_KEY in .env for embeddings")
        print("=" * 60)
        return 1
    print("RAG CHECK PASSED – search is working.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
