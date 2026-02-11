"""
Comprehensive test for the Scheme Saathi context extraction + filtering engine.
Run: python test_filters.py   (from backend/)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.main import (
    extract_context_from_text,
    build_cumulative_context,
    filter_schemes_for_user,
    _filter_state,
    _filter_gender,
    _filter_caste,
    _filter_age,
    _filter_occupation,
    _filter_education,
    _filter_disability,
    _filter_farmer_schemes,
    _filter_senior_schemes,
    _filter_child_schemes,
)

PASS = 0
FAIL = 0

def check(label, actual, expected):
    global PASS, FAIL
    ok = actual == expected
    if ok:
        PASS += 1
        print(f"  [OK] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}")
        print(f"         expected: {expected}")
        print(f"         got:      {actual}")


# ==========================
# CONTEXT EXTRACTION TESTS
# ==========================
print("=" * 60)
print("CONTEXT EXTRACTION TESTS")
print("=" * 60)

# Engineering student
ctx = extract_context_from_text("I'm a female engineering student in Karnataka")
check("occupation=student", ctx.get("occupation"), "student")
check("gender=female", ctx.get("gender"), "female")
check("state=Karnataka", ctx.get("state"), "Karnataka")
check("edu=higher", ctx.get("education_level"), "higher")

# Farmer
ctx = extract_context_from_text("I'm a 45 year old farmer in Bihar")
check("occupation=farmer", ctx.get("occupation"), "farmer")
check("age=45", ctx.get("age"), "45")
check("state=Bihar", ctx.get("state"), "Bihar")

# Senior citizen
ctx = extract_context_from_text("I am a retired senior citizen, age 67, from Kerala")
check("occupation=senior", ctx.get("occupation"), "senior citizen")
check("age=67", ctx.get("age"), "67")
check("state=Kerala", ctx.get("state"), "Kerala")

# SC student
ctx = extract_context_from_text("I'm an SC student looking for scholarships")
check("caste=SC", ctx.get("caste_category"), "SC")
check("occupation=student", ctx.get("occupation"), "student")

# OBC male, school-level
ctx = extract_context_from_text("I'm in class 9, male, OBC category from Rajasthan")
check("edu=school", ctx.get("education_level"), "school")
check("gender=male", ctx.get("gender"), "male")
check("caste=OBC", ctx.get("caste_category"), "OBC")
check("state=Rajasthan", ctx.get("state"), "Rajasthan")

# BPL family
ctx = extract_context_from_text("We are a BPL family from rural Jharkhand")
check("bpl=yes", ctx.get("bpl"), "yes")
check("residence=rural", ctx.get("residence"), "rural")
check("state=Jharkhand", ctx.get("state"), "Jharkhand")

# Disability
ctx = extract_context_from_text("I am a person with disability, divyang, from Delhi")
check("disability=yes", ctx.get("disability"), "yes")
check("state=Delhi", ctx.get("state"), "Delhi")

# Negation: not minority
ctx = extract_context_from_text("I'm not a minority, I'm general category")
check("caste=General", ctx.get("caste_category"), "General")

# Widow
ctx = extract_context_from_text("I am a widow from Gujarat, 50 years old")
check("family_status=widow", ctx.get("family_status"), "widow")
check("age=50", ctx.get("age"), "50")
check("state=Gujarat", ctx.get("state"), "Gujarat")

# Urban entrepreneur
ctx = extract_context_from_text("I want to start a business in urban Pune, Maharashtra")
check("occupation=entrepreneur", ctx.get("occupation"), "entrepreneur")
check("residence=urban", ctx.get("residence"), "urban")
check("state=Maharashtra", ctx.get("state"), "Maharashtra")

# Pregnant woman
ctx = extract_context_from_text("I am pregnant, looking for maternity benefits in Tamil Nadu")
check("family_status=pregnant", ctx.get("family_status"), "pregnant")
check("gender=female (from pregnant)", ctx.get("gender"), "female")
check("state=Tamil Nadu", ctx.get("state"), "Tamil Nadu")

# Negation: not disabled
ctx = extract_context_from_text("I'm not disabled, I'm a normal student")
check("no disability", ctx.get("disability"), None)

# Negation: not BPL
ctx = extract_context_from_text("I'm not BPL, my income is decent")
check("no bpl", ctx.get("bpl"), None)


# ========================
# CUMULATIVE CONTEXT TEST
# ========================
print()
print("=" * 60)
print("CUMULATIVE CONTEXT TESTS")
print("=" * 60)

history = [
    {"role": "user", "content": "Show me scholarships for SC students"},
    {"role": "assistant", "content": "Which state are you from?"},
    {"role": "user", "content": "Karnataka"},
    {"role": "assistant", "content": "Are you male or female?"},
]
current = "female, I'm studying btech"
ctx = build_cumulative_context(history, current)
check("cumul: occupation=student", ctx.get("occupation"), "student")
check("cumul: caste=SC", ctx.get("caste_category"), "SC")
check("cumul: state=Karnataka", ctx.get("state"), "Karnataka")
check("cumul: gender=female", ctx.get("gender"), "female")
check("cumul: edu=higher", ctx.get("education_level"), "higher")


# ========================
# FILTER TESTS
# ========================
print()
print("=" * 60)
print("SCHEME FILTER TESTS")
print("=" * 60)

# Helper scheme builders
def make_scheme(name="Test", state="All India", gender="any", caste="any",
                age_range="any", occupation="any", elig_text=""):
    return {
        "scheme_name": name,
        "brief_description": "",
        "eligibility_criteria": {
            "state": state,
            "gender": gender,
            "caste_category": caste,
            "age_range": age_range,
            "occupation": occupation,
            "raw_eligibility_text": elig_text,
        },
    }

# State tests
check("state: All India matches Karnataka", _filter_state(make_scheme(state="All India"), "Karnataka"), True)
check("state: Karnataka matches Karnataka", _filter_state(make_scheme(state="Karnataka"), "Karnataka"), True)
check("state: Meghalaya rejected for Karnataka", _filter_state(make_scheme(state="Meghalaya"), "Karnataka"), False)
check("state: Gujarat rejected for Karnataka", _filter_state(make_scheme(state="Gujarat"), "Karnataka"), False)

# Gender tests
check("gender: any matches female", _filter_gender(make_scheme(gender="any"), "female"), True)
check("gender: female matches female", _filter_gender(make_scheme(gender="female"), "female"), True)
check("gender: female rejected for male", _filter_gender(make_scheme(gender="female"), "male"), False)

# Caste tests
check("caste: any matches SC", _filter_caste(make_scheme(caste="any"), "SC"), True)
check("caste: SC matches SC", _filter_caste(make_scheme(caste="SC"), "SC"), True)
check("caste: SC/ST matches SC", _filter_caste(make_scheme(caste="SC/ST"), "SC"), True)
check("caste: SC rejected for General", _filter_caste(make_scheme(caste="SC"), "General"), False)
check("caste: OBC rejected for General", _filter_caste(make_scheme(caste="OBC"), "General"), False)
check("caste: Minority rejected for General", _filter_caste(make_scheme(caste="Minority"), "General"), False)
check("caste: any (higher for SC) matches General", _filter_caste(make_scheme(caste="any (higher subsidy for SC/ST)"), "General"), True)

# Age tests
check("age: any matches 22", _filter_age(make_scheme(age_range="any"), 22), True)
check("age: 18-40 matches 22", _filter_age(make_scheme(age_range="18-40"), 22), True)
check("age: 18-40 rejects 50", _filter_age(make_scheme(age_range="18-40"), 50), False)
check("age: 60+ matches 67", _filter_age(make_scheme(age_range="60+"), 67), True)
check("age: 60+ rejects 22", _filter_age(make_scheme(age_range="60+"), 22), False)
check("age: <10 matches 7", _filter_age(make_scheme(age_range="<10"), 7), True)
check("age: <10 rejects 22", _filter_age(make_scheme(age_range="<10"), 22), False)

# Occupation tests
check("occ: any matches student", _filter_occupation(make_scheme(occupation="any"), "student"), True)
check("occ: student matches student", _filter_occupation(make_scheme(occupation="student"), "student"), True)
check("occ: farmer rejects student", _filter_occupation(make_scheme(occupation="farmer"), "student"), False)
check("occ: farmer matches farmer", _filter_occupation(make_scheme(occupation="farmer"), "farmer"), True)
check("occ: student rejects farmer", _filter_occupation(make_scheme(occupation="student"), "farmer"), False)

# Education tests
pre_matric = make_scheme(name="Pre-Matric Scholarship for SC Students")
post_matric = make_scheme(name="Post Matric Scholarship for SC Students")
general = make_scheme(name="National Scholarship Portal")

check("edu: pre-matric rejected for higher ed", _filter_education(pre_matric, "higher"), False)
check("edu: post-matric kept for higher ed", _filter_education(post_matric, "higher"), True)
check("edu: general kept for higher ed", _filter_education(general, "higher"), True)
check("edu: post-matric rejected for school", _filter_education(post_matric, "school"), False)
check("edu: pre-matric kept for school", _filter_education(pre_matric, "school"), True)

# Disability tests
disability_scheme = make_scheme(name="Scholarship for Students with Disabilities")
normal_scheme = make_scheme(name="National Merit Scholarship")
check("disability scheme rejected for non-disabled", _filter_disability(disability_scheme, False), False)
check("disability scheme kept for disabled", _filter_disability(disability_scheme, True), True)
check("normal scheme kept for non-disabled", _filter_disability(normal_scheme, False), True)

# Farmer scheme filter
kisan_scheme = make_scheme(name="PM-KISAN Samman Nidhi")
check("kisan rejected for student", _filter_farmer_schemes(kisan_scheme, "student"), False)
check("kisan kept for farmer", _filter_farmer_schemes(kisan_scheme, "farmer"), True)

# Senior citizen filter
senior_scheme = make_scheme(name="Indira Gandhi Old Age Pension")
check("senior scheme rejected for 22yr student", _filter_senior_schemes(senior_scheme, 22, "student"), False)
check("senior scheme kept for 67yr senior", _filter_senior_schemes(senior_scheme, 67, "senior citizen"), True)
check("senior scheme kept for 60yr worker", _filter_senior_schemes(senior_scheme, 60, "worker"), True)

# Child scheme filter
child_scheme = make_scheme(name="Sukanya Samriddhi Yojana", elig_text="for girl child below 10")
check("child scheme rejected for 30yr adult", _filter_child_schemes(child_scheme, 30), False)


# ========================
# FULL PIPELINE TEST
# ========================
print()
print("=" * 60)
print("FULL PIPELINE TEST")
print("=" * 60)

schemes = [
    make_scheme("Pre-Matric SC Scholarship", state="All India", caste="SC", occupation="student"),
    make_scheme("Post Matric SC Scholarship", state="All India", caste="SC", occupation="student"),
    make_scheme("Karnataka Engineering Scholarship", state="Karnataka", occupation="student"),
    make_scheme("Meghalaya Tribal Scheme", state="Meghalaya", caste="ST"),
    make_scheme("PM-KISAN", state="All India", occupation="farmer"),
    make_scheme("Old Age Pension", state="All India", age_range="60+", occupation="any"),
    make_scheme("Disability Scholarship", state="All India", occupation="student"),
    make_scheme("Women Entrepreneur Loan", state="All India", gender="female", occupation="entrepreneur"),
]
# Fix: add scheme_name to disability scheme
schemes[6]["scheme_name"] = "Scholarship for Students with Disabilities"

# User: 22yr female SC engineering student from Karnataka
user_ctx = {
    "state": "Karnataka",
    "gender": "female",
    "caste_category": "SC",
    "age": "22",
    "occupation": "student",
    "education_level": "higher",
}

result = filter_schemes_for_user(schemes, user_ctx)
result_names = [s["scheme_name"] for s in result]

check("pipeline: Post Matric SC kept", "Post Matric SC Scholarship" in result_names, True)
check("pipeline: Karnataka Engg kept", "Karnataka Engineering Scholarship" in result_names, True)
check("pipeline: Pre-Matric SC removed", "Pre-Matric SC Scholarship" in result_names, False)
check("pipeline: Meghalaya removed", "Meghalaya Tribal Scheme" in result_names, False)
check("pipeline: PM-KISAN removed", "PM-KISAN" in result_names, False)
check("pipeline: Old Age Pension removed", "Old Age Pension" in result_names, False)
check("pipeline: Disability removed", "Scholarship for Students with Disabilities" in result_names, False)
check("pipeline: Women Entrepreneur removed", "Women Entrepreneur Loan" in result_names, False)

print()
print("=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL}")
print("=" * 60)

if FAIL > 0:
    sys.exit(1)
else:
    print("All tests passed!")
