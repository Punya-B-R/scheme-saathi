"""
Test script for Gemini service.
Run from backend directory: python test_gemini.py
Requires GEMINI_API_KEY set in .env (non-placeholder).
"""

import logging
from app.config import settings
from app.models import ChatMessage
from app.services.gemini_service import gemini_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

print("=" * 60)
print("GEMINI SERVICE TEST")
print("=" * 60)

# Test 1: Initialization
print("\n1. Initialization...")
try:
    has_key = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "placeholder")
    model_name = settings.GEMINI_MODEL
    print(f"   [OK] Model: {model_name}, API key set: {has_key}")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 2: Health check
print("\n2. Health check...")
try:
    healthy = gemini_service.check_health()
    if healthy:
        print("   [OK] check_health() = True")
    else:
        print("   [FAIL] check_health() = False (check GEMINI_API_KEY in .env)")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 3: System prompt (no schemes)
print("\n3. System prompt (no schemes)...")
try:
    prompt = gemini_service.create_system_prompt()
    assert "Scheme Saathi" in prompt
    assert len(prompt) > 200
    print(f"   [OK] Length={len(prompt)}, contains 'Scheme Saathi'")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 4: System prompt (with schemes)
print("\n4. System prompt (with schemes)...")
try:
    mock_scheme = {
        "scheme_name": "PM-KISAN",
        "benefits": {"summary": "Rs 6,000 per year for farmers"},
        "eligibility_criteria": {"raw_eligibility_text": "Farmers with < 2 hectares"},
    }
    prompt = gemini_service.create_system_prompt([mock_scheme])
    assert "PM-KISAN" in prompt
    assert "6,000" in prompt or "6000" in prompt
    print("   [OK] Prompt includes scheme info")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 5: Simple chat
print("\n5. Simple chat ('Hello')...")
try:
    reply = gemini_service.chat("Hello", [], None)
    assert reply and len(reply) > 0
    if "placeholder" in reply.lower() or "api key" in reply.lower():
        print("   [SKIP] No API key; placeholder message returned")
    else:
        print(f"   [OK] Reply length={len(reply)}, preview: {reply[:80]}...")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 6: Chat with context
print("\n6. Chat with context ('I'm a farmer in Bihar')...")
try:
    reply = gemini_service.chat("I'm a farmer in Bihar", [], None)
    assert reply and len(reply) > 0
    if "placeholder" in reply.lower() or "api key" in reply.lower():
        print("   [SKIP] No API key")
    else:
        print(f"   [OK] Reply length={len(reply)}, preview: {reply[:80]}...")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 7: Context extraction
print("\n7. Context extraction...")
try:
    conv = [ChatMessage(role="user", content="I'm a farmer in Bihar with 2 acres")]
    ctx = gemini_service.extract_user_context(conv)
    if not gemini_service._ensure_model():
        print("   [SKIP] No API key; extraction returns empty")
    elif isinstance(ctx, dict):
        has_occupation = ctx.get("occupation", "").lower() == "farmer"
        has_state = "bihar" in (ctx.get("state") or "").lower()
        print(f"   [OK] Extracted: {ctx}")
        if not has_occupation and not has_state:
            print("   [WARN] Expected occupation=farmer, state=Bihar (model may vary)")
    else:
        print(f"   [FAIL] Expected dict, got {type(ctx)}")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 8: Chat with schemes (use RAG if available)
print("\n8. Chat with schemes...")
try:
    schemes = []
    try:
        from app.services.rag_service import rag_service
        schemes = rag_service.search_schemes("farmer schemes", top_k=3)
    except Exception:
        pass
    if not schemes:
        schemes = [{"scheme_name": "PM-KISAN", "benefits": {"summary": "Rs 6,000/year"}, "eligibility_criteria": {"raw_eligibility_text": "Farmers"}}]
    reply = gemini_service.chat("Tell me about farmer schemes", [], schemes)
    assert reply and len(reply) > 0
    if "placeholder" in reply.lower() or "api key" in reply.lower():
        print("   [SKIP] No API key")
    else:
        mentions_scheme = "PM-KISAN" in reply or "scheme" in reply.lower() or "farmer" in reply.lower()
        print(f"   [OK] Reply length={len(reply)}")
        if not mentions_scheme:
            print("   [WARN] Response may not mention scheme names (model can vary)")
except Exception as e:
    print(f"   [FAIL] {e}")

print("\n" + "=" * 60)
print("Gemini service test complete!")
print("=" * 60)
