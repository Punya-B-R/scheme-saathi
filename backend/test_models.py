"""
Test script to verify Pydantic models work correctly.
Run from backend directory: python test_models.py
"""

from datetime import datetime

from app.models import (
    Benefits,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    EligibilityCriteria,
    HealthResponse,
)

print("=" * 60)
print("PYDANTIC MODELS TEST")
print("=" * 60)

# Test ChatMessage
print("\n1. Testing ChatMessage...")
msg = ChatMessage(role="user", content="Hello")
print(f"   [OK] ChatMessage created: {msg.role} - {msg.content}")

# Test ChatRequest
print("\n2. Testing ChatRequest...")
request = ChatRequest(
    message="I'm a farmer in Bihar",
    conversation_history=[msg],
    language="hi",
)
print(f"   [OK] ChatRequest created with message: '{request.message}'")
print(f"   [OK] Language: {request.language}")

# Test EligibilityCriteria
print("\n3. Testing EligibilityCriteria...")
eligibility = EligibilityCriteria(
    age_range="18-60",
    gender="any",
    caste_category="any",
    income_limit="< 2.5 lakh",
    occupation="farmer",
    state="Bihar",
    requires_aadhaar=True,
    raw_eligibility_text="Farmers in Bihar with income < 2.5 lakh",
)
print(f"   [OK] Eligibility created: {eligibility.occupation} in {eligibility.state}")

# Test Benefits
print("\n4. Testing Benefits...")
benefits = Benefits(
    summary="Rs 6,000 per year",
    financial_benefit="Rs 6,000",
    benefit_type="Direct cash transfer",
    frequency="Yearly",
)
print(f"   [OK] Benefits created: {benefits.summary}")

# Test HealthResponse
print("\n5. Testing HealthResponse...")
health = HealthResponse(
    status="healthy",
    app_name="Scheme Saathi",
    version="1.0.0",
    gemini_status="connected",
    vector_db_status="loaded",
    total_schemes=4500,
)
print(f"   [OK] Health response: {health.status} - {health.total_schemes} schemes")

print("\n" + "=" * 60)
print("All models working correctly!")
print("=" * 60)
