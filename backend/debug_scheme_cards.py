#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to identify where scheme cards flow goes wrong.
Run from backend dir: python debug_scheme_cards.py

Tests:
1. Context extraction + has_enough_context (6 fields)
2. Scheme name matching (extractMentionedSchemeNames equivalent)
3. doesResponseMentionSchemes fallback
4. Full flow simulation
"""

import re
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import (
    extract_context_from_text,
    build_cumulative_context,
    has_enough_context,
    get_missing_fields,
)

# ---------------------------------------------------------------------------
# Frontend logic replicated (Message.jsx)
# ---------------------------------------------------------------------------


def extract_mentioned_scheme_names(content: str, schemes: list[dict]) -> list[dict]:
    """Python equivalent of Message.jsx extractMentionedSchemeNames."""
    if not content or not schemes:
        return []

    content_lower = content.lower()
    result = []

    for scheme in schemes:
        scheme_name = (
            scheme.get("scheme_name") or scheme.get("name") or ""
        ).lower()

        if not scheme_name:
            result.append({"scheme": scheme, "matched": False, "reason": "no name"})
            continue

        name_words = [w for w in scheme_name.split() if len(w) > 2]
        key_part = " ".join(name_words[:3])

        if not key_part:
            result.append({"scheme": scheme, "matched": False, "reason": f"key_part empty (name={scheme_name!r})"})
            continue

        matched = key_part in content_lower
        result.append({
            "scheme": scheme,
            "matched": matched,
            "scheme_name": scheme_name,
            "key_part": key_part,
            "reason": f"content {'contains' if matched else 'does NOT contain'} {key_part!r}",
        })

    return result


def does_response_mention_schemes(content: str) -> bool:
    """Python equivalent of Message.jsx doesResponseMentionSchemes."""
    if not content or not isinstance(content, str):
        return False

    scheme_indicators = [
        "scheme", "schemes", "yojana", "yojnaa",
        "benefit", "benefits", "eligible", "eligibility",
        "qualify", "qualified", "entitled", "entitlement",
        "apply", "application", "register", "enroll",
        "found for you", "here are", "following",
        "these are", "i found", "i've found",
        "matches", "matching", "matched",
        "options for you", "programs", "initiatives",
        "for your profile", "based on your",
        "results", "recommendations",
        "₹", "rupees", "lakh", "per month",
        "per year", "annually", "monthly",
        "financial assistance", "subsidy", "pension",
        "scholarship", "loan", "grant",
        "योजना", "योजनाएं", "पात्र", "लाभ",
        "आवेदन", "मिलेगा", "मिलेंगे",
        "सहायता", "छात्रवृत्ति",
    ]

    lower_content = content.lower()
    for ind in scheme_indicators:
        if ind.lower() in lower_content:
            return True
    return False


def schemes_to_show(content: str, schemes: list[dict]) -> tuple[list[dict], str]:
    """
    Simulate Message.jsx scheme card logic.
    Returns (schemes_to_show, debug_reason).
    """
    if not schemes:
        return [], "no schemes in message"

    mentioned = extract_mentioned_scheme_names(content, schemes)
    matched_schemes = [m["scheme"] for m in mentioned if m["matched"]]

    if matched_schemes:
        return matched_schemes, "extractMentionedSchemeNames found matches"

    if does_response_mention_schemes(content):
        return schemes, "fallback: doesResponseMentionSchemes=True, showing all"

    return [], "both extraction and fallback failed"


# ---------------------------------------------------------------------------
# Test scenarios
# ---------------------------------------------------------------------------

SAMPLE_SCHEMES = [
    {"scheme_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)", "scheme_id": "1"},
    {"scheme_name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)", "scheme_id": "2"},
    {"scheme_name": "Post Matric Scholarship for SC Students", "scheme_id": "3"},
    {"scheme_name": "PM-KISAN", "scheme_id": "4"},  # Short form
]


def run_tests():
    print("=" * 70)
    print("SCHEME CARDS DEBUG - Identifying where it goes wrong")
    print("=" * 70)

    # ---- Test 1: Context extraction & has_enough_context ----
    print("\n### TEST 1: Backend - Context extraction & 6-field check ###\n")

    test_messages = [
        "I am a farmer in Karnataka",
        "I am 35 years old male OBC farmer in Karnataka with 1.5 lakh annual income",
        "35 year old male farmer Karnataka",
        "I am a student from Tamil Nadu, age 20, female, OBC, income 2 lakh",
        "farmer karnataka 40 male sc income 1 lakh",  # no "income" keyword - might fail
    ]

    for msg in test_messages:
        ctx = extract_context_from_text(msg)
        missing = get_missing_fields(ctx)
        ready = has_enough_context(ctx)

        print(f"Input: {msg!r}")
        print(f"  Extracted: {ctx}")
        print(f"  Missing: {missing}")
        print(f"  has_enough_context (RAG runs): {ready}")
        if not ready:
            print(f"  >>> BACKEND WON'T RETURN SCHEMES - missing: {missing}")
        print()

    # ---- Test 2: Scheme name matching ----
    print("\n### TEST 2: Frontend - Scheme name matching (extractMentionedSchemeNames) ###\n")

    ai_responses = [
        "Based on your profile, here are the schemes you qualify for:\n\n1. **PM-KISAN**\n   Benefit: ₹6,000/year\n   ...",
        "Here are 3 schemes:\n1. Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)\n2. PM-JAY\n3. Post Matric Scholarship",
        "You qualify for **PM Kisan** and **PM-JAY**.",  # "PM Kisan" vs "PM-KISAN"
        "आपके लिए PM-KISAN और Ayushman Bharat योजनाएं हैं.",  # Hindi
        "I found schemes for you: PM-KISAN, Post Matric Scholarship for SC Students.",
        "No schemes match your profile.",  # Should NOT show cards
    ]

    for ai_text in ai_responses:
        mentioned = extract_mentioned_scheme_names(ai_text, SAMPLE_SCHEMES)
        matched = [m for m in mentioned if m["matched"]]
        to_show, reason = schemes_to_show(ai_text, SAMPLE_SCHEMES)

        print(f"AI response (truncated): {ai_text[:80]!r}...")
        for m in mentioned:
            status = "[OK]" if m["matched"] else "[X]"
            name = (m.get("scheme_name") or "?")[:40]
            print(f"  {status} {name!r} -> key_part={m.get('key_part','')!r} -> {m['reason']}")
        print(f"  schemesToShow: {len(to_show)} schemes ({reason})")
        if len(to_show) == 0 and "No schemes" not in ai_text:
            print(f"  >>> CARDS WON'T SHOW - matching failed")
        print()

    # ---- Test 3: Full flow simulation ----
    print("\n### TEST 3: Full flow simulation ###\n")

    # Simulate: user gives full info
    history = []
    current = "I am a 35 year old male OBC farmer in Karnataka, income 1.5 lakh per year"
    ctx = build_cumulative_context(history, current)
    ready = has_enough_context(ctx)
    missing = get_missing_fields(ctx)

    print("Scenario: User gives full info in one message")
    print(f"  Context: {ctx}")
    print(f"  Missing: {missing}")
    print(f"  RAG will run: {ready}")
    if ready:
        print("  Backend would return schemes.")
        # Simulate AI response
        ai_resp = "Here are schemes: 1. PM-KISAN 2. PM-JAY 3. Post Matric Scholarship"
        to_show, reason = schemes_to_show(ai_resp, SAMPLE_SCHEMES)
        print(f"  If AI says: {ai_resp[:60]}...")
        print(f"  Cards shown: {len(to_show)} ({reason})")
    else:
        print("  >>> BACKEND WILL NOT RETURN SCHEMES - fix context extraction or relax 6-field rule")
    print()

    # Simulate: user gives partial info
    history2 = [{"role": "user", "content": "I am a farmer in Karnataka"}]
    current2 = "I am 35, male, OBC"  # missing income_level
    ctx2 = build_cumulative_context(history2, current2)
    ready2 = has_enough_context(ctx2)
    missing2 = get_missing_fields(ctx2)

    print("Scenario: User gives occupation, state, age, gender, caste (no income)")
    print(f"  Context: {ctx2}")
    print(f"  Missing: {missing2}")
    print(f"  RAG will run: {ready2}")
    if not ready2:
        print("  >>> BACKEND WILL NOT RETURN SCHEMES")
        print(f"  Likely culprit: income_level not extracted from 'I am 35, male, OBC'")
    print()

    # ---- Summary ----
    print("\n" + "=" * 70)
    print("SUMMARY - Common failure points:")
    print("=" * 70)
    print("1. income_level: Requires 'income|earn|salary' + number + 'lakh|per year' in text.")
    print("   - '1.5 lakh' alone won't extract. Try 'income 1.5 lakh' or 'annual income 1.5 lakh'.")
    print("2. Scheme name matching: 'PM Kisan' (space) != 'PM-KISAN' (hyphen) in key_part.")
    print("   - AI must use exact scheme names from the list.")
    print("3. Authenticated users: Backend chat history doesn't store schemes - past chats have no cards.")
    print("4. Fallback: doesResponseMentionSchemes needs keywords like 'scheme','here are','eligible'.")
    print()


if __name__ == "__main__":
    run_tests()
