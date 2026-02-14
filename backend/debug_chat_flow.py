#!/usr/bin/env python3
"""
Simulate /chat flow for one message and print the DEBUG lines.
Run: python debug_chat_flow.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import (
    build_cumulative_context,
    is_ready_to_recommend,
    get_missing_fields,
    filter_schemes_for_user,
)
from app.services.rag_service import rag_service

MESSAGE = "I am a 35 year old male OBC farmer in Karnataka with 1.5 lakh annual income"

def main():
    # Simulate chat flow
    history = []
    query = MESSAGE.strip()

    user_ctx = build_cumulative_context(history, query)
    missing = get_missing_fields(user_ctx)
    ready = is_ready_to_recommend(user_ctx)

    print("DEBUG 2 - user_ctx:", user_ctx)
    print("DEBUG 3 - is_ready:", ready)
    print("Missing fields:", missing)

    candidates = []
    if ready:
        search_parts = [query]
        for key in ("occupation", "state", "gender", "caste_category", "education_level"):
            val = user_ctx.get(key)
            if val and str(val).lower() not in ("unknown", "any", ""):
                search_parts.append(str(val))
        if user_ctx.get("specific_need"):
            search_parts.append(str(user_ctx["specific_need"]))
        if user_ctx.get("disability") == "yes":
            search_parts.append("disability divyang PWD")
        if user_ctx.get("bpl") == "yes":
            search_parts.append("BPL below poverty economically weaker")

        search_query = " ".join(search_parts)
        raw = rag_service.search_schemes(
            query=search_query,
            user_context=user_ctx,
            top_k=50,
        )
        print("DEBUG 4 - RAG results count:", len(raw) if raw else 0)
        candidates = filter_schemes_for_user(raw or [], user_ctx)
        candidates = (candidates or [])[:20]
        print("DEBUG 5 - After filtering:", len(candidates))
    else:
        print("DEBUG 4 - RAG results count: (skipped - ready=False)")
        print("DEBUG 5 - After filtering: 0")

    print("DEBUG 6 - Final schemes count:", len(candidates))
    print("DEBUG 7 - needs_more_info:", not ready)
    if candidates:
        print("\n--- Final schemes (names) ---")
        for i, s in enumerate(candidates, 1):
            name = (s.get("name") or s.get("scheme_name") or "(no name)") if isinstance(s, dict) else str(s)
            print(f"  {i}. {name}")
    print("\n--- Full output done ---")

if __name__ == "__main__":
    main()
