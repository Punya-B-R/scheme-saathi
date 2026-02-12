"""
Data Enrichment Script for Scheme Saathi
=========================================
Reads all_schemes.json, analyzes the free-text fields (scheme_name,
brief_description, raw_eligibility_text, raw_benefits_text) and
re-classifies the broken structured fields:

  - state (from "All India" → actual state)
  - occupation (from "any" → farmer/student/etc.)
  - benefit_type (from "Other" → scholarship/loan/pension/etc.)
  - gender (from "any" → female where applicable)
  - caste_category (from "any" → SC/ST/OBC where applicable)
  - age_range (from "any" → actual range)

Saves enriched data back to all_schemes.json (with backup).

Run:  python enrich_data.py
"""

import json
import re
import shutil
import sys
import io
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATA_PATH = Path(__file__).parent / "data_f" / "all_schemes.json"
BACKUP_PATH = Path(__file__).parent / "data_f" / "all_schemes_backup.json"

# ============================================================
# STATE EXTRACTION
# ============================================================

INDIAN_STATES = {
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    "delhi": "Delhi",
    "jammu and kashmir": "Jammu and Kashmir",
    "jammu & kashmir": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "chandigarh": "Chandigarh",
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
    "dadra and nagar haveli": "Dadra and Nagar Haveli",
    "daman and diu": "Daman and Diu",
    "daman & diu": "Daman and Diu",
    "andaman and nicobar": "Andaman and Nicobar",
    "andaman & nicobar": "Andaman and Nicobar",
    "lakshadweep": "Lakshadweep",
}

# Patterns that indicate state-specificity in eligibility text
STATE_ELIG_PATTERNS = [
    r"(?:resident|native|domicile|residing)\s+(?:of|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    r"(?:belong(?:s|ing)?\s+to|from)\s+(?:the\s+)?(?:state\s+of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    r"(?:state|ut|union\s+territory)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    r"located\s+in\s+(?:the\s+)?(?:state\s+of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
]


def extract_state(text: str, current_state: str) -> str:
    """Extract state from text. Only override if currently 'All India' or 'any'."""
    if current_state.lower() not in ("all india", "any", "all", "nationwide", ""):
        # Already has a specific state
        return current_state

    t_lower = text.lower()

    # Direct match: look for state names in the text
    # Sort by length (longest first) to match "Andhra Pradesh" before "Pradesh"
    for state_lower, state_proper in sorted(INDIAN_STATES.items(), key=lambda x: -len(x[0])):
        # Check for patterns like "resident of Karnataka", "native of Bihar"
        pattern = rf"(?:resident|native|domicile|residing|belong|from|state|located)\s+(?:of|in|to)\s+(?:the\s+)?(?:state\s+of\s+)?{re.escape(state_lower)}"
        if re.search(pattern, t_lower):
            return state_proper

    # Check scheme name for state suffix like "- Karnataka", "- Tamil Nadu"
    for state_lower, state_proper in sorted(INDIAN_STATES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"[-–]\s*{re.escape(state_lower)}\b", t_lower):
            return state_proper

    # Check for "Government of [State]"
    for state_lower, state_proper in sorted(INDIAN_STATES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"government\s+of\s+{re.escape(state_lower)}", t_lower):
            return state_proper

    return current_state


# ============================================================
# OCCUPATION EXTRACTION
# ============================================================

OCCUPATION_RULES = [
    # (pattern_in_text, occupation_value)
    (r"\b(?:farmer|kisan|agricultur(?:ist|al\s+labour)|cultivat(?:or|ing)|land\s*hold(?:er|ing))\b", "farmer"),
    (r"\bstudent\b|\bstudying\b|\bscholar\b|\bpupil\b|\bundergraduate\b|\bpostgraduate\b|\bclass\s+\d|\bschool\b.*\bchild\b", "student"),
    (r"\b(?:senior\s+citizen|old\s*age|elderly|vridh|aged\s+(?:above|over)\s+(?:5[5-9]|6\d|7\d))\b", "senior citizen"),
    (r"\b(?:widow|vidhwa)\b", "widow"),
    (r"\b(?:entrepreneur|startup|business\s*(?:man|woman|owner)|msme|self[- ]?employ)\b", "entrepreneur"),
    (r"\b(?:artisan|handicraft|handloom|weaver|potter|blacksmith|carpenter|goldsmith)\b", "artisan"),
    (r"\b(?:fisherm(?:a|e)n|fish\s*(?:worker|vendor|farmer)|fishing)\b", "fisherman"),
    (r"\b(?:construction\s+worker|building\s+worker|labour(?:er)?|unorganized\s+(?:sector\s+)?worker|beedi\s+worker)\b", "worker"),
    (r"\b(?:tribal|adivasi|forest\s+dweller)\b", "tribal"),
    (r"\b(?:ex[- ]?servicem(?:a|e)n|veteran|armed\s+force|military|army|navy|air\s+force)\b", "ex-serviceman"),
    (r"\b(?:sportsperson|athlete|sports\s*(?:man|woman|person))\b", "sportsperson"),
    (r"\b(?:research(?:er)?|scientist|phd|doctoral)\b", "researcher"),
    (r"\b(?:teacher|educator|faculty)\b", "teacher"),
    (r"\b(?:driver|transport\s+worker|auto\s+driver|taxi\s+driver)\b", "driver"),
    (r"\b(?:domestic\s+worker|maid|house\s*(?:wife|maker))\b", "homemaker"),
    (r"\b(?:journalist|media\s+person)\b", "journalist"),
    (r"\b(?:lawyer|advocate|legal\s+practitioner)\b", "lawyer"),
    (r"\b(?:nurse|doctor|medical\s+practitioner|health\s+worker|asha\s+worker|anganwadi)\b", "health worker"),
]


def extract_occupation(text: str, current_occ: str) -> str:
    """Extract occupation from text."""
    if current_occ.lower() not in ("any", ""):
        return current_occ

    t = text.lower()
    for pattern, occ in OCCUPATION_RULES:
        if re.search(pattern, t):
            return occ

    return current_occ


# ============================================================
# BENEFIT TYPE EXTRACTION
# ============================================================

BENEFIT_TYPE_RULES = [
    # (pattern_in_name_or_benefits, benefit_type)
    (r"\bscholarship\b|\bfellowship\b|\bstipend\b|\bfreeship\b|\bfee\s+(?:waiver|reimburs|concession)\b|\btuition\b.*\bfee\b", "Scholarship"),
    (r"\bloan\b(?!\s+mela)|\bcredit\b.*\b(?:scheme|facility)\b|\bmudra\b", "Loan"),
    (r"\bpension\b", "Pension"),
    (r"\binsurance\b|\bhealth\s*cover\b|\bhospitali[sz]ation\b|\bayushman\b|\bpmjay\b|\bhealth\s+card\b", "Insurance"),
    (r"\bhousing\b|\bawas\b|\bshelter\s+home\b|\bhouse\s+(?:construction|building)\b|\bpmay\b", "Housing"),
    (r"\bmaternity\b|\bpregnant\b|\bjanani\b|\blactating\b|\bdelivery\b.*\b(?:benefit|assist)\b", "Maternity Benefit"),
    (r"\bmarriage\b.*\b(?:assist|benefit|grant|scheme)\b|\bshadi\b|\bvivah\b|\bkanyadan\b|\bdaughter.*marriage\b|marriage.*daughter\b", "Marriage Assistance"),
    (r"\btraining\b|\bskill\s+develop\b|\bvocational\b|\bapprentice\b|\bplacement\b|\binternship\b", "Skill Training"),
    (r"\bsubsidy\b|\bgrant\b.*\b(?:scheme|assist)\b|\bcapital\s+subsidy\b|\binvestment\s+subsidy\b", "Subsidy"),
    (r"\bfree\s+(?:electricity|water|gas|ration|rice|wheat|food)\b|\bration\b.*\b(?:card|scheme)\b|\bfood\s+security\b", "Food/Essentials"),
    (r"\bfree\s+(?:bus|travel|transport)\b|\bbus\s+pass\b|\btravel\s+concession\b", "Travel Concession"),
    (r"\bfree\s+(?:textbook|uniform|bicycle|laptop|tablet|sewing\s+machine)\b|\bdistribution\s+of\b", "In-kind Support"),
    (r"\blegal\s+(?:aid|assist|help)\b|\bvictim\s+(?:compensation|assist)\b|\bprotection\b.*\bwomen\b", "Legal Aid"),
    (r"\brehabilitation\b|\bresettlement\b|\brelief\b.*\b(?:disaster|flood|earthquake|cyclone)\b", "Rehabilitation"),
    (r"\b(?:direct\s+benefit|dbt|financial\s+assist|cash\s+transfer|monetary\s+(?:help|assist|benefit))\b", "Financial Assistance"),
    (r"\bseed\s+fund\b|\bstartup\b.*\b(?:fund|grant|support)\b|\bventure\b", "Startup Fund"),
    (r"\bfree\s+(?:treatment|surgery|medicine|medical)\b|\bhealth\s+(?:check|camp|care)\b|\bfree\s+blood\b", "Healthcare"),
]


def extract_benefit_type(name: str, benefits_text: str, current_bt: str) -> str:
    """Extract benefit type from scheme name and benefits text."""
    if current_bt.lower() not in ("other", ""):
        return current_bt

    combined = f"{name} {benefits_text}".lower()
    for pattern, bt in BENEFIT_TYPE_RULES:
        if re.search(pattern, combined):
            return bt

    return current_bt


# ============================================================
# GENDER EXTRACTION
# ============================================================

def extract_gender(text: str, name: str, current_gender: str) -> str:
    """Extract target gender from text."""
    if current_gender.lower() not in ("any", ""):
        return current_gender

    combined = f"{name} {text}".lower()

    # Explicit female-only patterns
    female_patterns = [
        r"\b(?:woman|women|girl|female|mahila|beti|kanya|balika|stree|lady|ladies)\b",
        r"\bwidow\b|\bvidhwa\b",
        r"\blactating\s+mother\b|\bpregnant\s+(?:woman|women|mother)\b",
        r"\bdaughter\b.*\b(?:marriage|scheme|benefit)\b",
        r"\bsingle\s+girl\b",
    ]

    male_only = [
        r"\bex[- ]?servicem(?:a|e)n\b",  # technically could be female too, but traditionally male
    ]

    # Check if the scheme is EXCLUSIVELY for women/girls
    is_female = any(re.search(p, combined) for p in female_patterns)
    # But also check if it says "both" or "all"
    is_both = bool(re.search(r"\bboth\s+(?:male|men)\s+(?:and|&)\s+(?:female|women)\b|\ball\s+gender\b", combined))

    if is_female and not is_both:
        return "female"

    return current_gender


# ============================================================
# CASTE EXTRACTION
# ============================================================

def extract_caste(text: str, name: str, current_caste: str) -> str:
    """Extract target caste category from text."""
    if current_caste.lower() not in ("any", ""):
        return current_caste

    combined = f"{name} {text}".lower()

    # SC-specific
    if re.search(r"\bscheduled\s+caste\b|\b(?:for|of)\s+sc\b|\bsc\s+(?:student|candidate|beneficiar|applicant|communit)\b", combined):
        if re.search(r"\bscheduled\s+tribe\b|\bst\b", combined):
            return "SC/ST"
        return "SC"

    # ST-specific
    if re.search(r"\bscheduled\s+tribe\b|\btribal\b|\badivasi\b|\b(?:for|of)\s+st\b|\bst\s+(?:student|candidate|beneficiar)\b", combined):
        return "ST"

    # SC/ST combined
    if re.search(r"\bsc\s*/\s*st\b|\bsc\s+(?:and|&)\s+st\b", combined):
        return "SC/ST"

    # OBC
    if re.search(r"\bobc\b|\bother\s+backward\s+class\b|\bbackward\s+class\b", combined):
        if re.search(r"\bsc\b|\bst\b", combined):
            return "SC/ST/OBC"
        return "OBC"

    # Minority
    if re.search(r"\bminority\b|\bmuslim\b|\bchristian\b|\bsikh\b|\bbuddhist\b|\bjain\b|\bparsi\b|\bzoroastrian\b", combined):
        return "Minority"

    # EWS / Economically Weaker
    if re.search(r"\bews\b|\beconomically\s+weaker\b", combined):
        return "EWS"

    # General / All
    if re.search(r"\ball\s+(?:categories|castes|communities)\b|\bgeneral\s+(?:and|category)\b", combined):
        return "any"

    # Brahmin (some state-specific schemes)
    if re.search(r"\bbrahmin\b", combined):
        return "Brahmin"

    return current_caste


# ============================================================
# AGE RANGE EXTRACTION
# ============================================================

def extract_age_range(text: str, current_age: str) -> str:
    """Extract age range from eligibility text."""
    if current_age.lower() not in ("any", ""):
        return current_age

    t = text.lower()

    # "X to Y years" or "X-Y years"
    m = re.search(r"(\d{1,2})\s*(?:to|[-–])\s*(\d{1,3})\s*(?:years?\s+(?:of\s+)?age|years?\s+old|years)", t)
    if m:
        return f"{m.group(1)}-{m.group(2)}"

    # "above/over/minimum X years"
    m = re.search(r"(?:above|over|at\s+least|minimum|not\s+(?:less|below)\s+than)\s+(\d{1,2})\s*(?:years?\s+(?:of\s+)?age|years?\s+old|years)", t)
    if m:
        return f"{m.group(1)}+"

    # "below/under/maximum X years"
    m = re.search(r"(?:below|under|up\s+to|not\s+(?:more|above|exceed)\s+than|maximum)\s+(\d{1,3})\s*(?:years?\s+(?:of\s+)?age|years?\s+old|years)", t)
    if m:
        return f"0-{m.group(1)}"

    # "aged X+"
    m = re.search(r"aged\s+(?:above\s+)?(\d{1,2})\+?", t)
    if m:
        return f"{m.group(1)}+"

    return current_age


# ============================================================
# MAIN ENRICHMENT
# ============================================================

def get_all_text(scheme: dict) -> str:
    """Combine all available text fields for analysis."""
    parts = []
    parts.append(scheme.get("scheme_name") or "")
    parts.append(scheme.get("brief_description") or "")
    parts.append(scheme.get("detailed_description") or "")

    elig = scheme.get("eligibility_criteria") or {}
    if isinstance(elig, dict):
        parts.append(elig.get("raw_eligibility_text") or "")
        for cond in (elig.get("other_conditions") or []):
            if isinstance(cond, str):
                parts.append(cond)

    benefits = scheme.get("benefits") or {}
    if isinstance(benefits, dict):
        parts.append(benefits.get("raw_benefits_text") or "")
        parts.append(benefits.get("summary") or "")

    return " ".join(parts)


def enrich_scheme(scheme: dict) -> dict:
    """Enrich a single scheme's structured fields from its text content."""
    elig = scheme.get("eligibility_criteria") or {}
    if not isinstance(elig, dict):
        elig = {}

    benefits = scheme.get("benefits") or {}
    if not isinstance(benefits, dict):
        benefits = {}

    name = scheme.get("scheme_name") or ""
    all_text = get_all_text(scheme)
    benefits_text = f"{benefits.get('raw_benefits_text', '')} {benefits.get('summary', '')}"

    # ── Enrich state ──
    old_state = elig.get("state") or "All India"
    new_state = extract_state(all_text, old_state)
    elig["state"] = new_state

    # ── Enrich occupation ──
    old_occ = elig.get("occupation") or "any"
    new_occ = extract_occupation(all_text, old_occ)
    elig["occupation"] = new_occ

    # ── Enrich benefit_type ──
    old_bt = benefits.get("benefit_type") or "Other"
    new_bt = extract_benefit_type(name, benefits_text, old_bt)
    benefits["benefit_type"] = new_bt

    # ── Enrich gender ──
    old_gender = elig.get("gender") or "any"
    new_gender = extract_gender(all_text, name, old_gender)
    elig["gender"] = new_gender

    # ── Enrich caste ──
    old_caste = elig.get("caste_category") or "any"
    new_caste = extract_caste(all_text, name, old_caste)
    elig["caste_category"] = new_caste

    # ── Enrich age_range ──
    raw_elig = elig.get("raw_eligibility_text") or ""
    old_age = elig.get("age_range") or "any"
    new_age = extract_age_range(raw_elig, old_age)
    elig["age_range"] = new_age

    # Write back
    scheme["eligibility_criteria"] = elig
    scheme["benefits"] = benefits

    return scheme


def main():
    print("=" * 70)
    print("SCHEME SAATHI DATA ENRICHMENT")
    print("=" * 70)

    # Load
    print(f"\nLoading {DATA_PATH}...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    schemes = data.get("schemes", [])
    print(f"Loaded {len(schemes)} schemes")

    # Backup
    print(f"Creating backup at {BACKUP_PATH}...")
    shutil.copy2(DATA_PATH, BACKUP_PATH)
    print("Backup created.")

    # ── Before stats ──
    def count_field(field_path, values_to_count):
        """Count how many schemes have a field matching given values."""
        count = 0
        for s in schemes:
            obj = s
            for key in field_path:
                obj = (obj or {}).get(key) if isinstance(obj, dict) else None
            if obj and str(obj).strip().lower() in values_to_count:
                count += 1
        return count

    print("\n--- BEFORE ENRICHMENT ---")
    bt_other = count_field(["benefits", "benefit_type"], {"other"})
    occ_any = count_field(["eligibility_criteria", "occupation"], {"any"})
    state_all = count_field(["eligibility_criteria", "state"], {"all india"})
    gender_any = count_field(["eligibility_criteria", "gender"], {"any"})
    caste_any = count_field(["eligibility_criteria", "caste_category"], {"any"})
    age_any = count_field(["eligibility_criteria", "age_range"], {"any"})

    print(f"  benefit_type = 'Other':   {bt_other:5d} / {len(schemes)}")
    print(f"  occupation = 'any':       {occ_any:5d} / {len(schemes)}")
    print(f"  state = 'All India':      {state_all:5d} / {len(schemes)}")
    print(f"  gender = 'any':           {gender_any:5d} / {len(schemes)}")
    print(f"  caste_category = 'any':   {caste_any:5d} / {len(schemes)}")
    print(f"  age_range = 'any':        {age_any:5d} / {len(schemes)}")

    # ── Enrich ──
    print(f"\nEnriching {len(schemes)} schemes...")
    changes = {
        "state": 0,
        "occupation": 0,
        "benefit_type": 0,
        "gender": 0,
        "caste_category": 0,
        "age_range": 0,
    }

    for i, scheme in enumerate(schemes):
        elig_before = dict((scheme.get("eligibility_criteria") or {}))
        benefits_before = dict((scheme.get("benefits") or {})) if isinstance(scheme.get("benefits"), dict) else {}

        scheme = enrich_scheme(scheme)
        schemes[i] = scheme

        elig_after = scheme.get("eligibility_criteria") or {}
        benefits_after = scheme.get("benefits") or {}

        if elig_after.get("state") != elig_before.get("state"):
            changes["state"] += 1
        if elig_after.get("occupation") != elig_before.get("occupation"):
            changes["occupation"] += 1
        if benefits_after.get("benefit_type") != benefits_before.get("benefit_type"):
            changes["benefit_type"] += 1
        if elig_after.get("gender") != elig_before.get("gender"):
            changes["gender"] += 1
        if elig_after.get("caste_category") != elig_before.get("caste_category"):
            changes["caste_category"] += 1
        if elig_after.get("age_range") != elig_before.get("age_range"):
            changes["age_range"] += 1

        if (i + 1) % 500 == 0:
            print(f"  Processed {i+1}/{len(schemes)}...")

    print(f"  Processed {len(schemes)}/{len(schemes)} - DONE")

    # ── After stats ──
    print("\n--- AFTER ENRICHMENT ---")
    bt_other2 = count_field(["benefits", "benefit_type"], {"other"})
    occ_any2 = count_field(["eligibility_criteria", "occupation"], {"any"})
    state_all2 = count_field(["eligibility_criteria", "state"], {"all india"})
    gender_any2 = count_field(["eligibility_criteria", "gender"], {"any"})
    caste_any2 = count_field(["eligibility_criteria", "caste_category"], {"any"})
    age_any2 = count_field(["eligibility_criteria", "age_range"], {"any"})

    print(f"  benefit_type = 'Other':   {bt_other2:5d} / {len(schemes)}  (was {bt_other}, fixed {bt_other - bt_other2})")
    print(f"  occupation = 'any':       {occ_any2:5d} / {len(schemes)}  (was {occ_any}, fixed {occ_any - occ_any2})")
    print(f"  state = 'All India':      {state_all2:5d} / {len(schemes)}  (was {state_all}, fixed {state_all - state_all2})")
    print(f"  gender = 'any':           {gender_any2:5d} / {len(schemes)}  (was {gender_any}, fixed {gender_any - gender_any2})")
    print(f"  caste_category = 'any':   {caste_any2:5d} / {len(schemes)}  (was {caste_any}, fixed {caste_any - caste_any2})")
    print(f"  age_range = 'any':        {age_any2:5d} / {len(schemes)}  (was {age_any}, fixed {age_any - age_any2})")

    print(f"\n--- CHANGES SUMMARY ---")
    for field, count in changes.items():
        print(f"  {field:20s}: {count:5d} schemes updated")
    total_changes = sum(changes.values())
    print(f"  {'TOTAL':20s}: {total_changes:5d} field updates")

    # ── Distribution of new values ──
    print("\n--- NEW BENEFIT_TYPE DISTRIBUTION ---")
    bt_dist = {}
    for s in schemes:
        b = s.get("benefits") or {}
        bt = b.get("benefit_type", "?") if isinstance(b, dict) else "?"
        bt_dist[bt] = bt_dist.get(bt, 0) + 1
    for k, v in sorted(bt_dist.items(), key=lambda x: -x[1]):
        print(f"  {v:5d}  {k}")

    print("\n--- NEW OCCUPATION DISTRIBUTION ---")
    occ_dist = {}
    for s in schemes:
        e = s.get("eligibility_criteria") or {}
        o = e.get("occupation", "?") if isinstance(e, dict) else "?"
        occ_dist[o] = occ_dist.get(o, 0) + 1
    for k, v in sorted(occ_dist.items(), key=lambda x: -x[1]):
        print(f"  {v:5d}  {k}")

    print("\n--- NEW GENDER DISTRIBUTION ---")
    g_dist = {}
    for s in schemes:
        e = s.get("eligibility_criteria") or {}
        g = e.get("gender", "?") if isinstance(e, dict) else "?"
        g_dist[g] = g_dist.get(g, 0) + 1
    for k, v in sorted(g_dist.items(), key=lambda x: -x[1]):
        print(f"  {v:5d}  {k}")

    print("\n--- NEW CASTE DISTRIBUTION ---")
    c_dist = {}
    for s in schemes:
        e = s.get("eligibility_criteria") or {}
        c = e.get("caste_category", "?") if isinstance(e, dict) else "?"
        c_dist[c] = c_dist.get(c, 0) + 1
    for k, v in sorted(c_dist.items(), key=lambda x: -x[1]):
        print(f"  {v:5d}  {k}")

    # ── Save ──
    data["schemes"] = schemes
    data["metadata"]["enriched_at"] = datetime.now().isoformat()
    data["metadata"]["enrichment_changes"] = changes

    # Recalculate statistics
    state_dist = {}
    for s in schemes:
        e = s.get("eligibility_criteria") or {}
        st = (e.get("state") or "All India") if isinstance(e, dict) else "All India"
        state_dist[st] = state_dist.get(st, 0) + 1
    top_states = dict(sorted(state_dist.items(), key=lambda x: -x[1])[:25])
    data["statistics"]["schemes_per_state"] = top_states

    print(f"\nSaving enriched data to {DATA_PATH}...")
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    file_size_mb = DATA_PATH.stat().st_size / (1024 * 1024)
    print(f"Saved! File size: {file_size_mb:.1f} MB")

    print("\n" + "=" * 70)
    print("ENRICHMENT COMPLETE!")
    print("=" * 70)
    print(f"\nBackup saved at: {BACKUP_PATH}")
    print("IMPORTANT: You need to rebuild ChromaDB after this!")
    print("  1. Delete the chroma_db folder")
    print("  2. Restart the backend server")
    print("  (ChromaDB will auto-rebuild from the enriched data)")


if __name__ == "__main__":
    main()
