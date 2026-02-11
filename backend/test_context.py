"""Quick test for context extraction."""
import sys
sys.path.insert(0, ".")
from app.main import extract_context_from_text, build_cumulative_context, context_completeness

tests = [
    ("Show me scholarships for SC/ST students", {"occupation": "student", "caste_category": "SC/ST"}),
    ("karnataka", {"state": "Karnataka"}),
    ("I'm a female engineering student in karnataka", {"gender": "female", "occupation": "student", "state": "Karnataka"}),
    ("I am 21 years old", {"age": "21"}),
    ("I'm from OBC category", {"caste_category": "OBC"}),
    ("I'm a farmer in Bihar with 2 acres", {"occupation": "farmer", "state": "Bihar"}),
    ("What pension schemes exist for senior citizens?", {"occupation": "senior citizen"}),
]

print("=== Single Message Tests ===\n")
for msg, expected in tests:
    ctx = extract_context_from_text(msg)
    ok = all(ctx.get(k) == v for k, v in expected.items())
    status = "[OK]" if ok else "[FAIL]"
    print(f"{status} '{msg[:50]}'")
    if not ok:
        print(f"       Expected: {expected}")
        print(f"       Got:      {ctx}")
    else:
        print(f"       -> {ctx}")

print("\n=== Cumulative Context Test ===\n")
history = [
    {"role": "user", "content": "Show me scholarships for SC/ST students"},
    {"role": "assistant", "content": "Which state are you from?"},
    {"role": "user", "content": "karnataka"},
    {"role": "assistant", "content": "What is your age?"},
]
ctx = build_cumulative_context(history, "I am 21 years old")
print(f"Cumulative context: {ctx}")
print(f"Completeness: {context_completeness(ctx)}/5")
expected_keys = {"occupation", "caste_category", "state", "age"}
missing = expected_keys - set(ctx.keys())
if missing:
    print(f"[FAIL] Missing: {missing}")
else:
    print("[OK] All expected fields present")
