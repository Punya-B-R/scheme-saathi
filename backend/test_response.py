"""Quick test to verify the /chat endpoint returns schemes properly."""
import sys, os, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(__file__))

import requests

BASE = "http://localhost:8000"

# Simulate a conversation where we give all 4 fields at once
print("Testing /chat endpoint with full context...")
resp = requests.post(f"{BASE}/chat", json={
    "message": "I am a female SC student from Karnataka looking for scholarships",
    "conversation_history": [],
    "language": "en"
})

data = resp.json()
print(f"Status: {resp.status_code}")
print(f"needs_more_info: {data.get('needs_more_info')}")
print(f"schemes count: {len(data.get('schemes', []))}")
print(f"extracted_context: {data.get('extracted_context')}")
print(f"message preview: {data.get('message', '')[:200]}...")

if data.get('schemes'):
    print("\n--- Schemes returned ---")
    for i, s in enumerate(data['schemes'][:3], 1):
        print(f"  {i}. {s.get('scheme_name', '?')[:60]}")
        b = s.get('benefits') or {}
        print(f"     benefit_type: {b.get('benefit_type', '?') if isinstance(b, dict) else '?'}")
        print(f"     has source_url: {bool(s.get('source_url') or s.get('official_website'))}")
else:
    print("\nNO SCHEMES returned!")
    print("This means needs_more_info=True or the filters returned 0 candidates")
