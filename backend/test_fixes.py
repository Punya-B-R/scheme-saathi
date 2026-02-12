"""
Quick test to verify readiness logic, need extraction, and need-based filtering.
Run: python test_fixes.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.main import (
    extract_context_from_text,
    build_cumulative_context,
    has_enough_context,
    is_ready_to_recommend,
    _filter_by_need,
    _is_valid,
    context_completeness,
    missing_context_fields,
)

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}")


print("=" * 60)
print("TEST 1: _is_valid helper")
print("=" * 60)
check("None is not valid", not _is_valid(None))
check("empty is not valid", not _is_valid(""))
check("unknown is not valid", not _is_valid("unknown"))
check("any is not valid", not _is_valid("any"))
check("all india is not valid", not _is_valid("All India"))
check("Karnataka is valid", _is_valid("Karnataka"))
check("student is valid", _is_valid("student"))


print("\n" + "=" * 60)
print("TEST 2: has_enough_context (needs occupation AND state)")
print("=" * 60)
check("empty -> False", not has_enough_context({}))
check("only occupation -> False", not has_enough_context({"occupation": "student"}))
check("only state -> False", not has_enough_context({"state": "Karnataka"}))
check("occ + state -> True", has_enough_context({"occupation": "student", "state": "Karnataka"}))
check("occ=any + state -> False", not has_enough_context({"occupation": "any", "state": "Karnataka"}))


print("\n" + "=" * 60)
print("TEST 3: is_ready_to_recommend (needs occ+state+help_type+1more)")
print("=" * 60)
check("empty -> False", not is_ready_to_recommend({}))
check("occ only -> False", not is_ready_to_recommend({"occupation": "student"}))
check("occ + state -> False", not is_ready_to_recommend({"occupation": "student", "state": "Karnataka"}))

# Missing help_type, even with gender
check("occ+state+gender but NO help_type -> False", not is_ready_to_recommend({
    "occupation": "student", "state": "Karnataka", "gender": "female"
}))
# Has help_type but no gender/age/caste
check("occ+state+help_type but NO gender/age/caste -> False", not is_ready_to_recommend({
    "occupation": "student", "state": "Karnataka", "help_type": "scholarship"
}))
# Full: occ + state + help_type + gender
check("occ+state+help_type+gender -> True", is_ready_to_recommend({
    "occupation": "student", "state": "Karnataka", "help_type": "scholarship", "gender": "female"
}))
# Full: occ + state + help_type + age
check("occ+state+help_type+age -> True", is_ready_to_recommend({
    "occupation": "student", "state": "Karnataka", "help_type": "scholarship", "age": "20"
}))
# Full: occ + state + help_type + caste
check("occ+state+help_type+caste -> True", is_ready_to_recommend({
    "occupation": "farmer", "state": "Bihar", "help_type": "loan", "caste_category": "OBC"
}))


print("\n" + "=" * 60)
print("TEST 4: Specific need extraction (comprehensive)")
print("=" * 60)
ctx = extract_context_from_text("I'm looking for scholarships")
check("scholarship detected", ctx.get("specific_need") == "scholarship")
check("help_type also set", ctx.get("help_type") == "scholarship")

ctx = extract_context_from_text("I need a loan for my business")
check("loan detected", ctx.get("specific_need") == "loan")

ctx = extract_context_from_text("What pension schemes are available?")
check("pension detected", ctx.get("specific_need") == "pension")

ctx = extract_context_from_text("I need health insurance")
check("health_insurance detected", ctx.get("specific_need") == "health_insurance")

ctx = extract_context_from_text("I want housing scheme")
check("housing detected", ctx.get("specific_need") == "housing")

ctx = extract_context_from_text("I need help with marriage expenses")
check("marriage detected", ctx.get("specific_need") == "marriage")

ctx = extract_context_from_text("I want skill training")
check("skill_training detected", ctx.get("specific_need") == "skill_training")

ctx = extract_context_from_text("I need money for my family")
check("financial_assistance detected", ctx.get("specific_need") == "financial_assistance")

ctx = extract_context_from_text("Looking for a job")
check("employment detected", ctx.get("specific_need") == "employment")

ctx = extract_context_from_text("I want to start a business")
check("business_support detected", ctx.get("specific_need") == "business_support")

ctx = extract_context_from_text("I need crop insurance")
check("agriculture_support detected", ctx.get("specific_need") == "agriculture_support")

ctx = extract_context_from_text("I want to know about government schemes")
check("no specific need for generic query", ctx.get("specific_need") is None)


print("\n" + "=" * 60)
print("TEST 5: Need-based filtering")
print("=" * 60)

scholarship_scheme = {
    "scheme_name": "Post Matric Scholarship for SC Students",
    "brief_description": "Scholarship for SC students in post-matric education",
    "benefits": {"benefit_type": "Scholarship", "summary": "Tuition fee + maintenance"},
    "eligibility_criteria": {"raw_eligibility_text": "SC student post matric"},
}

loan_scheme = {
    "scheme_name": "Mudra Loan Scheme",
    "brief_description": "Loans for small businesses",
    "benefits": {"benefit_type": "Subsidized Loan", "summary": "Loan up to 10 lakhs"},
    "eligibility_criteria": {"raw_eligibility_text": "small business entrepreneurs"},
}

pension_scheme = {
    "scheme_name": "Atal Pension Yojana",
    "brief_description": "Pension for unorganized sector",
    "benefits": {"benefit_type": "Pension", "summary": "Monthly pension"},
    "eligibility_criteria": {"raw_eligibility_text": "aged 18-40"},
}

generic_scheme = {
    "scheme_name": "Financial Assistance Scheme",
    "brief_description": "Financial help for students",
    "benefits": {"benefit_type": "Direct Cash Transfer", "summary": "Cash transfer"},
    "eligibility_criteria": {"raw_eligibility_text": "students"},
}

# User wants scholarship
check("scholarship passes for scholarship need", _filter_by_need(scholarship_scheme, "scholarship"))
check("loan REJECTED for scholarship need", not _filter_by_need(loan_scheme, "scholarship"))
check("pension REJECTED for scholarship need", not _filter_by_need(pension_scheme, "scholarship"))
check("generic passes for scholarship need", _filter_by_need(generic_scheme, "scholarship"))

# User wants loan
check("loan passes for loan need", _filter_by_need(loan_scheme, "loan"))
check("scholarship REJECTED for loan need", not _filter_by_need(scholarship_scheme, "loan"))

# No specific need -> everything passes
check("scholarship passes with no need", _filter_by_need(scholarship_scheme, ""))
check("loan passes with no need", _filter_by_need(loan_scheme, ""))


print("\n" + "=" * 60)
print("TEST 6: Full conversation flow simulation")
print("=" * 60)

# Simulate: student -> Karnataka -> scholarship -> female
history1 = [{"role": "user", "content": "I'm a student"}]
ctx1 = build_cumulative_context(history1, "")
check("After msg 1: not ready", not is_ready_to_recommend(ctx1))
missing1 = missing_context_fields(ctx1)
check("Next question is state", missing1[0] == "state")

history2 = history1 + [
    {"role": "assistant", "content": "Which state are you from?"},
    {"role": "user", "content": "Karnataka"},
]
ctx2 = build_cumulative_context(history2, "")
check("After msg 2: still not ready (no help_type)", not is_ready_to_recommend(ctx2))
missing2 = missing_context_fields(ctx2)
check("Next question is help_type", missing2[0] == "help_type")

history3 = history2 + [
    {"role": "assistant", "content": "What kind of help are you looking for?"},
    {"role": "user", "content": "I need scholarship"},
]
ctx3 = build_cumulative_context(history3, "")
check("After msg 3: still not ready (no gender/age/caste)", not is_ready_to_recommend(ctx3))
missing3 = missing_context_fields(ctx3)
check("Next question is gender", missing3[0] == "gender")

history4 = history3 + [
    {"role": "assistant", "content": "What is your gender?"},
    {"role": "user", "content": "female"},
]
ctx4 = build_cumulative_context(history4, "")
check("After msg 4: NOW ready (occ+state+help+gender)", is_ready_to_recommend(ctx4))
check("Has scholarship need", ctx4.get("specific_need") == "scholarship")


print("\n" + "=" * 60)
print("TEST 7: Context field ordering")
print("=" * 60)
ctx_partial = {"occupation": "student"}
missing = missing_context_fields(ctx_partial)
check("After occ: next is state", missing[0] == "state")

ctx_partial2 = {"occupation": "student", "state": "Karnataka"}
missing2 = missing_context_fields(ctx_partial2)
check("After occ+state: next is help_type", missing2[0] == "help_type")

ctx_partial3 = {"occupation": "student", "state": "Karnataka", "help_type": "scholarship"}
missing3 = missing_context_fields(ctx_partial3)
check("After occ+state+help: next is gender", missing3[0] == "gender")


print("\n" + "=" * 60)
print("TEST 8: Multi-info single message")
print("=" * 60)
ctx = extract_context_from_text("I'm a female farmer from Bihar looking for loan")
check("occupation=farmer", ctx.get("occupation") == "farmer")
check("state=Bihar", ctx.get("state") == "Bihar")
check("gender=female", ctx.get("gender") == "female")
check("need=loan", ctx.get("specific_need") == "loan")
check("help_type=loan", ctx.get("help_type") == "loan")
check("ready with all info", is_ready_to_recommend(ctx))


print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
print("=" * 60)

if failed > 0:
    sys.exit(1)
else:
    print("All tests passed!")
