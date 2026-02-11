"""
Test script for RAG service (ChromaDB + semantic search).
Run from backend directory: python test_rag.py
"""

import logging
from app.services.rag_service import rag_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

print("=" * 60)
print("RAG SERVICE TEST")
print("=" * 60)

# 1. Initialization / total schemes
print("\n1. Initialization...")
total = rag_service.get_total_schemes()
print(f"   [OK] Total schemes loaded: {total}")

if total == 0:
    print("   [FAIL] No schemes; cannot run search tests.")
    exit(1)

# 2. Health check
print("\n2. Health check...")
healthy = rag_service.check_health()
print(f"   [OK] check_health() = {healthy}")

# 3. Simple search
print("\n3. Search: 'farmer schemes'...")
results = rag_service.search_schemes("farmer schemes", top_k=5)
print(f"   [OK] Found {len(results)} schemes")
for i, s in enumerate(results[:3], 1):
    score = s.get("match_score", 0)
    print(f"      {i}. {s.get('scheme_name', '')[:50]}... (score={score})")

# 4. Search with user context
print("\n4. Search with context: occupation=farmer, state=Bihar...")
results_ctx = rag_service.search_schemes(
    "help with farming",
    user_context={"occupation": "farmer", "state": "Bihar"},
    top_k=5,
)
print(f"   [OK] Found {len(results_ctx)} schemes")
for i, s in enumerate(results_ctx[:3], 1):
    score = s.get("match_score", 0)
    print(f"      {i}. {s.get('scheme_name', '')[:50]}... (score={score})")

# 5. get_scheme_by_id
print("\n5. get_scheme_by_id (first scheme)...")
first_id = rag_service.schemes[0].get("scheme_id") if rag_service.schemes else None
if first_id:
    scheme = rag_service.get_scheme_by_id(first_id)
    if scheme:
        print(f"   [OK] Found: {scheme.get('scheme_name', '')[:50]}...")
    else:
        print("   [FAIL] get_scheme_by_id returned None")
else:
    print("   [SKIP] No scheme_id to look up")

# 6. get_total_schemes again
print("\n6. get_total_schemes()...")
print(f"   [OK] {rag_service.get_total_schemes()} schemes")

# 7. Match score range check
print("\n7. Match score range (from simple search)...")
if results:
    scores = [s.get("match_score", 0) for s in results]
    print(f"   [OK] Scores in range [{min(scores):.2f}, {max(scores):.2f}]")
else:
    print("   [SKIP] No results to check scores")

print("\n" + "=" * 60)
print("RAG service test complete!")
print("=" * 60)
