"""Quick look at 15 diverse schemes to understand text patterns."""
import json, random, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
random.seed(42)

with open("data_f/all_schemes.json", "r", encoding="utf-8") as f:
    data = json.load(f)

schemes = data["schemes"]
samples = random.sample(schemes, 15)

for s in samples:
    e = s.get("eligibility_criteria") or {}
    raw = (e.get("raw_eligibility_text") or "")[:350]
    state = e.get("state", "?")
    occ = e.get("occupation", "?")
    b = s.get("benefits") or {}
    bt = b.get("benefit_type", "?") if isinstance(b, dict) else "?"
    rawb = (b.get("raw_benefits_text") or "")[:200] if isinstance(b, dict) else ""
    name = s.get("scheme_name", "?")[:60]
    cat = s.get("category", "?")
    print(f"--- {name} [{cat}] ---")
    print(f"  FIELDS: state={state} | occ={occ} | btype={bt}")
    print(f"  ELIG: {raw}")
    print(f"  BENE: {rawb}")
    print()
