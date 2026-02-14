#!/usr/bin/env python3
"""
Check whether scheme recommendations come from RAG (ChromaDB) or from the LLM.
Runs multiple test queries in one go (no need to check the website).

- For each query: runs RAG directly, then (if backend is up) calls /chat and compares.
- Prints results per query and a final summary verdict.

Run from backend directory:
  python check_rag.py

Optional: BASE_URL env or first arg (e.g. python check_rag.py http://localhost:8000).
"""

import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Multiple test cases: message + context for direct RAG call (context must have occupation + state for RAG to run)
TEST_CASES = [
    {
        "name": "Farmer, Karnataka",
        "message": "I am a farmer in Karnataka",
        "context": {"occupation": "farmer", "state": "Karnataka"},
    },
    {
        "name": "Student, Bihar",
        "message": "I'm a student in Bihar looking for scholarships",
        "context": {"occupation": "student", "state": "Bihar", "specific_need": "scholarship"},
    },
    {
        "name": "Senior citizen, Kerala",
        "message": "Senior citizen in Kerala looking for pension",
        "context": {"occupation": "senior citizen", "state": "Kerala", "specific_need": "pension"},
    },
    {
        "name": "Entrepreneur, Maharashtra",
        "message": "I want to start a small business in Maharashtra",
        "context": {"occupation": "entrepreneur", "state": "Maharashtra"},
    },
    {
        "name": "Student, Delhi (female)",
        "message": "Female student in Delhi",
        "context": {"occupation": "student", "state": "Delhi", "gender": "female"},
    },
    {
        "name": "Farmer, Tamil Nadu",
        "message": "I'm from Tamil Nadu and I'm a farmer",
        "context": {"occupation": "farmer", "state": "Tamil Nadu"},
    },
    {
        "name": "Student, no state (may not trigger RAG)",
        "message": "I'm a student looking for scholarships",
        "context": {"occupation": "student"},  # no state -> is_ready may be False
    },
]


def norm_id(s: dict) -> str:
    return str(s.get("scheme_id") or s.get("id") or "")


def norm_name(s: dict) -> str:
    return (s.get("scheme_name") or s.get("name") or s.get("title") or "").strip()


def get_rag_service():
    from app.services.rag_service import rag_service
    return rag_service


def run_rag_for_query(rag_service, message: str, context: dict, top_k: int = 20):
    """Return list of scheme dicts from RAG for one query."""
    if not rag_service.check_health():
        return []
    return rag_service.search_schemes(
        query=message,
        user_context=context,
        top_k=top_k,
    )


def run_chat_for_message(base_url: str, message: str):
    """POST /chat with message; return (response dict, None) or (None, error str)."""
    try:
        import httpx
    except ImportError:
        return None, "httpx not installed"

    url = f"{base_url.rstrip('/')}/chat"
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(url, json={
                "message": message,
                "conversation_history": [],
                "language": "en",
            })
            r.raise_for_status()
            return r.json(), None
    except httpx.ConnectError as e:
        return None, f"Connect error: {e}"
    except httpx.HTTPStatusError as e:
        return None, f"HTTP {e.response.status_code}"
    except Exception as e:
        return None, str(e)


def main():
    base_url = os.environ.get("BASE_URL", "http://localhost:8000")
    if len(sys.argv) > 1:
        base_url = sys.argv[1].strip()

    print("=" * 70)
    print("RAG CHECK – multiple queries (no website needed)")
    print("=" * 70)
    print(f"  Base URL (for /chat): {base_url}")
    print()

    # Load RAG once
    rag_service = get_rag_service()
    ok = rag_service.check_health()
    total = rag_service.get_total_schemes()
    coll_count = rag_service._collection.count() if rag_service._collection else 0

    print("RAG health (once)")
    print("-" * 70)
    print(f"  Healthy: {ok}  |  Schemes in memory: {total}  |  ChromaDB count: {coll_count}")
    if not ok or total == 0 or coll_count == 0:
        print("  -> RAG is NOT ready. Fix ChromaDB/embeddings first.")
        print()
    print()

    # Results per test case
    results = []
    for i, tc in enumerate(TEST_CASES, 1):
        name = tc["name"]
        message = tc["message"]
        context = tc["context"]
        rag_schemes = run_rag_for_query(rag_service, message, context)
        rag_ids = {norm_id(s) for s in rag_schemes if norm_id(s)}

        chat_data, chat_err = run_chat_for_message(base_url, message)
        chat_schemes = (chat_data.get("schemes") or []) if chat_data else []
        needs_more = chat_data.get("needs_more_info", True) if chat_data else None
        chat_ids = {norm_id(s) for s in chat_schemes if norm_id(s)} if chat_schemes else set()

        only_in_chat = chat_ids - rag_ids if rag_ids else chat_ids
        in_both = chat_ids & rag_ids if rag_ids else set()
        from_rag = chat_ids and (only_in_chat == set()) and (chat_ids <= rag_ids)

        results.append({
            "name": name,
            "message": message,
            "rag_count": len(rag_schemes),
            "chat_count": len(chat_schemes),
            "chat_err": chat_err,
            "needs_more": needs_more,
            "from_rag": from_rag,
            "only_in_chat": only_in_chat,
            "rag_ids": rag_ids,
            "rag_first": rag_schemes[:3] if rag_schemes else [],
        })

        # Print per-query block
        print(f"Query {i}: {name}")
        print("-" * 70)
        print(f"  Message: \"{message[:60]}{'...' if len(message) > 60 else ''}\"")
        print(f"  Context: {context}")
        print(f"  RAG returned:     {len(rag_schemes)} schemes")
        if rag_schemes:
            for j, s in enumerate(rag_schemes[:3], 1):
                print(f"    {j}. {norm_id(s)}  {norm_name(s)[:45]}")
        if chat_err:
            print(f"  /chat:           error – {chat_err}")
        else:
            print(f"  /chat schemes:   {len(chat_schemes)}  |  needs_more_info: {needs_more}")
            if chat_schemes:
                for j, s in enumerate(chat_schemes[:3], 1):
                    print(f"    {j}. {norm_id(s)}  {norm_name(s)[:45]}")
            if only_in_chat:
                print(f"  WARNING: Chat has IDs not from RAG: {list(only_in_chat)[:5]}")
            elif chat_ids and from_rag:
                print(f"  OK: Chat schemes are from RAG ({len(in_both)} overlap)")
        print()

    # Summary table
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  {'Query':<35}  {'RAG':>5}  {'Chat':>5}  {'From RAG?':<10}")
    print("-" * 70)
    for r in results:
        chat_str = str(r["chat_count"]) if r["chat_err"] is None else "err"
        from_rag_str = "yes" if r["from_rag"] else ("no" if r["chat_count"] and not r["chat_err"] else "–")
        print(f"  {r['name']:<35}  {r['rag_count']:>5}  {chat_str:>5}  {from_rag_str:<10}")
    print()

    # Overall verdict
    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    rag_ok_count = sum(1 for r in results if r["rag_count"] > 0)
    chat_ok_count = sum(1 for r in results if r["chat_err"] is None)
    from_rag_count = sum(1 for r in results if r["from_rag"])
    any_only_in_chat = any(r["only_in_chat"] for r in results)

    if not ok or total == 0:
        print("  RAG is NOT working (unhealthy or empty). Recommendations are not from RAG.")
    elif rag_ok_count == 0:
        print("  RAG returned 0 schemes for all queries. Check ChromaDB and context (occupation+state).")
    elif any_only_in_chat:
        print("  At least one chat response had scheme IDs not from RAG. Possible LLM/fallback or bug.")
    elif chat_ok_count == 0:
        print("  RAG works but /chat was never reached (backend down?). RAG-only: OK.")
    elif from_rag_count == chat_ok_count:
        print("  RAG is working. All chat scheme lists match RAG (recommendations are from RAG).")
    else:
        print("  RAG works for some queries. Check which ones have chat != RAG above.")
    print()
    sys.exit(0 if ok and rag_ok_count > 0 else 1)


if __name__ == "__main__":
    main()
