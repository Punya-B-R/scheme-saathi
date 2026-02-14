#!/usr/bin/env python3
"""
Quick check: is RAG working? (ChromaDB loaded, model ready, search returns schemes.)
Run from backend:  python check_rag_simple.py
Exits 0 if RAG is OK, 1 otherwise.
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_ROOT))

def main():
    from app.services.rag_service import rag_service

    print("RAG check:")
    ok = rag_service.check_health()
    n_schemes = rag_service.get_total_schemes()
    n_collection = rag_service._collection.count() if rag_service._collection else 0

    print(f"  Health: {ok}")
    print(f"  Schemes in memory: {n_schemes}")
    print(f"  ChromaDB count: {n_collection}")

    if not ok or n_schemes == 0 or n_collection == 0:
        print("  -> FAIL (RAG not ready)")
        sys.exit(1)

    results = rag_service.search_schemes(
        query="I am a farmer in Karnataka",
        user_context={"occupation": "farmer", "state": "Karnataka"},
        top_k=5,
    )
    print(f"  Test search returned: {len(results)} schemes")
    if results:
        print(f"  First: {results[0].get('scheme_name', '')[:50]}")
    if len(results) == 0:
        print("  -> FAIL (search returned 0 schemes)")
        sys.exit(1)

    print("  -> OK (RAG is working)")
    sys.exit(0)

if __name__ == "__main__":
    main()
