"""
Diagnostic: Run the EXACT same pipeline as the /chat endpoint
and show what comes back for a given user context.

This reveals WHY wrong schemes are returned.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from app.services.rag_service import rag_service
from app.main import filter_schemes_for_user, _filter_state, _get_elig

print(f"Total schemes loaded: {len(rag_service.schemes)}")
print(f"ChromaDB collection count: {rag_service._collection.count() if rag_service._collection else 'N/A'}")

# ─── TEST CASE 1: Student from Karnataka looking for scholarships ───
print("\n" + "=" * 80)
print("CASE 1: Student + Karnataka + scholarship + female")
print("=" * 80)

user_ctx = {
    "occupation": "student",
    "state": "Karnataka",
    "specific_need": "scholarship",
    "help_type": "scholarship",
    "gender": "female",
}

search_query = "Student looking for scholarships student Karnataka female scholarship"

raw = rag_service.search_schemes(
    query=search_query,
    user_context=user_ctx,
    top_k=30,
)

print(f"\nRAG returned {len(raw)} schemes (after RAG's internal filter)")
print("\n--- RAG results (before main filter) ---")
for i, s in enumerate(raw[:15], 1):
    elig = s.get("eligibility_criteria") or {}
    state = (elig.get("state") or "All India") if isinstance(elig, dict) else "?"
    occ = (elig.get("occupation") or "any") if isinstance(elig, dict) else "?"
    benefits = s.get("benefits") or {}
    btype = (benefits.get("benefit_type") or "?") if isinstance(benefits, dict) else "?"
    score = s.get("match_score", 0)
    print(f"  {i:2d}. [{score:.3f}] {s.get('scheme_name', '?')[:60]}")
    print(f"      State: {state[:50]} | Occ: {occ[:30]} | Type: {btype}")

filtered = filter_schemes_for_user(raw, user_ctx)
print(f"\nAfter main filter: {len(filtered)} schemes")
print("\n--- Final results ---")
for i, s in enumerate(filtered[:10], 1):
    elig = s.get("eligibility_criteria") or {}
    state = (elig.get("state") or "All India") if isinstance(elig, dict) else "?"
    benefits = s.get("benefits") or {}
    btype = (benefits.get("benefit_type") or "?") if isinstance(benefits, dict) else "?"
    print(f"  {i:2d}. {s.get('scheme_name', '?')[:65]}")
    print(f"      State: {state[:50]} | Type: {btype}")


# ─── TEST CASE 2: Farmer from Karnataka ───
print("\n" + "=" * 80)
print("CASE 2: Farmer + Karnataka + financial_assistance + male")
print("=" * 80)

user_ctx2 = {
    "occupation": "farmer",
    "state": "Karnataka",
    "specific_need": "financial_assistance",
    "help_type": "financial_assistance",
    "gender": "male",
}

search_query2 = "farmer Karnataka male money financial assistance crop agriculture"

raw2 = rag_service.search_schemes(
    query=search_query2,
    user_context=user_ctx2,
    top_k=30,
)

print(f"\nRAG returned {len(raw2)} schemes")
print("\n--- RAG results ---")
for i, s in enumerate(raw2[:15], 1):
    elig = s.get("eligibility_criteria") or {}
    state = (elig.get("state") or "All India") if isinstance(elig, dict) else "?"
    occ = (elig.get("occupation") or "any") if isinstance(elig, dict) else "?"
    score = s.get("match_score", 0)
    print(f"  {i:2d}. [{score:.3f}] {s.get('scheme_name', '?')[:60]}")
    print(f"      State: {state[:50]} | Occ: {occ[:30]}")

filtered2 = filter_schemes_for_user(raw2, user_ctx2)
print(f"\nAfter main filter: {len(filtered2)} schemes")
for i, s in enumerate(filtered2[:10], 1):
    elig = s.get("eligibility_criteria") or {}
    state = (elig.get("state") or "All India") if isinstance(elig, dict) else "?"
    print(f"  {i:2d}. {s.get('scheme_name', '?')[:65]}")
    print(f"      State: {state[:50]}")


# ─── CHECK: How many schemes in data have state=Karnataka? ───
print("\n" + "=" * 80)
print("DATA ANALYSIS: State distribution for Karnataka-eligible schemes")
print("=" * 80)

karnataka_count = 0
all_india_count = 0
other_state_count = 0
other_states = {}

for s in rag_service.schemes:
    elig = s.get("eligibility_criteria") or {}
    if not isinstance(elig, dict):
        continue
    state = (elig.get("state") or "All India").strip().lower()

    if "karnataka" in state:
        karnataka_count += 1
    elif any(kw in state for kw in ["all india", "all states", "national", "central"]):
        all_india_count += 1
    else:
        other_state_count += 1
        st = state[:30]
        other_states[st] = other_states.get(st, 0) + 1

print(f"Karnataka-specific: {karnataka_count}")
print(f"All India: {all_india_count}")
print(f"Other states: {other_state_count}")

# Show which 'other state' schemes pass through the state filter
print("\n--- Checking: Do any 'other state' schemes leak through state filter? ---")
leaked = 0
for s in raw[:15]:
    elig = s.get("eligibility_criteria") or {}
    if not isinstance(elig, dict):
        continue
    state = (elig.get("state") or "All India").strip().lower()
    passes = _filter_state(s, "Karnataka")
    is_karnataka = "karnataka" in state
    is_all_india = any(kw in state for kw in ["all india", "all states", "national", "central"])
    if passes and not is_karnataka and not is_all_india:
        leaked += 1
        print(f"  LEAK: {s.get('scheme_name', '?')[:50]} | state field = '{state}'")

if leaked == 0:
    print("  No state leaks detected in top 15 RAG results.")


# ─── CHECK: What embedding text looks like ───
print("\n" + "=" * 80)
print("EMBEDDING CHECK: What text was embedded for first few schemes?")
print("=" * 80)

from app.utils.data_loader import prepare_scheme_text_for_embedding
for s in rag_service.schemes[:3]:
    text = prepare_scheme_text_for_embedding(s)
    print(f"\n--- {s.get('scheme_name', '?')[:50]} ---")
    print(f"  Embedded text (first 300 chars): {text[:300]}...")
    print(f"  Total length: {len(text)} chars")
