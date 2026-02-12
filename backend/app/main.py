"""
FastAPI application for Scheme Saathi backend.
Comprehensive context extraction + multi-dimensional scheme filtering.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    SchemeSearchRequest,
    SchemeSearchResponse,
)
from app.database import get_db, init_db
from app.chat_history import (
    append_message,
    get_or_create_chat_for_message,
)
from app.auth_router import get_current_user_id
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.gemini_service import gemini_service
from app.services.rag_service import rag_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered government scheme discovery for Indian citizens",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

from app.auth_router import router as auth_router
from app.chats_router import router as chats_router

app.include_router(auth_router)
app.include_router(chats_router)


# ============================================================
# 1. CONTEXT EXTRACTION ENGINE
#    Extracts every possible dimension from user text via regex.
#    Zero API calls. ~1ms per message.
# ============================================================

INDIAN_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim",
    "tamil nadu", "telangana", "tripura", "uttar pradesh", "uttarakhand",
    "west bengal", "delhi", "jammu and kashmir", "ladakh", "chandigarh",
    "puducherry", "andaman and nicobar",
]

STATE_DISPLAY = {s: s.title() for s in INDIAN_STATES}
STATE_DISPLAY.update({
    "delhi": "Delhi", "tamil nadu": "Tamil Nadu", "uttar pradesh": "Uttar Pradesh",
    "madhya pradesh": "Madhya Pradesh", "andhra pradesh": "Andhra Pradesh",
    "himachal pradesh": "Himachal Pradesh", "arunachal pradesh": "Arunachal Pradesh",
    "west bengal": "West Bengal", "jammu and kashmir": "Jammu and Kashmir",
})

OCCUPATIONS = {
    r"\bfarmer\b|\bkisan\b|\bfarming\b|\bagricultur\w*\b|\bcrop\b|\bkhet\b|\bkheti\b": "farmer",
    r"\bstudents?\b|\bstudying\b|\bcollege\b|\buniversity\b|\bengineering\b|\bmedical\s+student\b|\bbtech\b|\bmba\b|\bschool\b|\bscholarship\b|\bclass\s+\d|\bmatric\b|\bdegree\b|\bpost.?graduate\b|\bgraduate\b|\bdiploma\b|\bphd\b": "student",
    r"\bsenior\s*citizens?\b|\bretired\b|\bold\s*age\b|\bpensioners?\b|\belderly\b|\bvridh\b|\bpension\b": "senior citizen",
    r"\bbusiness\b|\bentrepreneur\b|\bself.?employed\b|\bshop\s*keeper\b|\bstartup\b|\bmsme\b|\btrader\b|\budyami\b|\bvendor\b": "entrepreneur",
    r"\bworker\b|\blabou?r\b|\bemployee\b|\bdaily\s*wage\b|\bsalaried\b|\bjob\b|\bconstruction\s+worker\b|\bdomestic\s+worker\b": "worker",
    r"\bfisherm[ae]n\b|\bfishing\b|\bmatsyakara\b": "fisherman",
    r"\bartisan\b|\bhandicraft\b|\bweaver\b|\bpotter\b|\bvishwakarma\b|\bcarpenter\b|\bblacksmith\b": "artisan",
    r"\bhousewife\b|\bhomemaker\b|\bhouse\s*wife\b": "homemaker",
}

GENDERS = {
    r"\bfemale\b|\bwoman\b|\bwomen\b|\bgirl\b|\bmahila\b|\bmother\b|\bpregnant\b|\bwidow\b|\blady\b|\bdaughter\b|\bsister\b": "female",
    r"\bmale\b(?!\s*(?:and|or|\/)\s*female)|\bboy\b|\bson\b": "male",
}

CATEGORIES = {
    r"\bsc\s*/\s*st\b|\bsc\s+st\b|\bsc\s*&\s*st\b|\bsc\s+and\s+st\b": "SC/ST",
    r"\bsc\b|\bschedul\w+\s*caste\b|\bdalit\b": "SC",
    r"\bst\b|\bschedul\w+\s*tribe\b|\btribal\b|\badivasi\b": "ST",
    r"\bobc\b|\bother\s*backward\b": "OBC",
    r"\bgeneral\s*category\b|\bunreserved\b": "General",
    r"\bminority\b|\bmuslim\b|\bchristian\b|\bsikh\b|\bbuddhist\b|\bjain\b|\bparsi\b": "Minority",
}

# Education level: "higher" = post-matric / college+, "school" = pre-matric (class 1-10)
EDUCATION_HIGHER_PATTERNS = [
    r"\bengineering\b", r"\bbtech\b", r"\bb\.?tech\b", r"\bb\.?e\b",
    r"\bmtech\b", r"\bm\.?tech\b", r"\bmba\b", r"\bbba\b", r"\bm\.?sc\b",
    r"\bb\.?sc\b", r"\bm\.?a\b", r"\bb\.?a\b", r"\bm\.?com\b", r"\bb\.?com\b",
    r"\bph\.?d\b", r"\bpost.?graduate\b", r"\bgraduate\b", r"\bdiploma\b",
    r"\bcollege\b", r"\buniversity\b", r"\bdegree\b", r"\bprofessional\s+course\b",
    r"\bmedical\s+student\b", r"\bmbbs\b", r"\blaw\b", r"\bllb\b",
    r"\bnursing\b", r"\bpolytechnic\b", r"\biti\b", r"\bpost.?matric\b",
    r"\bclass\s*1[1-2]\b", r"\b1[1-2]th\b", r"\bhigher\s+secondary\b",
    r"\bhigher\s+education\b", r"\bunder.?graduate\b", r"\bug\b", r"\bpg\b",
    r"\bca\b", r"\bcs\b", r"\bicwa\b", r"\bchartered\b",
]
EDUCATION_SCHOOL_PATTERNS = [
    r"\bpre.?matric\b", r"\bclass\s*[1-9]\b(?!\d)", r"\bclass\s*10\b",
    r"\b[1-9]th\s+(?:class|standard|std)\b", r"\b10th\s+(?:class|standard|std)\b",
    r"\bprimary\s+school\b", r"\bmiddle\s+school\b", r"\bhigh\s+school\b",
]

# BPL / income status
BPL_PATTERNS = [
    r"\bbpl\b", r"\bbelow\s+poverty\b", r"\bpoor\b", r"\blow\s+income\b",
    r"\beconomically\s+weak\b", r"\bews\b", r"\bgarib\b",
    r"\bration\s+card\b.*\b(?:yellow|pink|priority)\b",
]

# Disability
DISABILITY_PATTERNS = [
    r"\bdisabl\w+\b", r"\bpwd\b", r"\bperson\s+with\s+disabilit\w+\b",
    r"\bhandicap\w*\b", r"\bdivyang\b", r"\bblind\b", r"\bdeaf\b",
    r"\borthopedic\w*\b", r"\bcerebral\s+palsy\b", r"\bmental\s+retard\w*\b",
    r"\bintellectual\s+disabilit\w*\b",
]

# Residence
RESIDENCE_PATTERNS = {
    r"\brural\b|\bvillage\b|\bgram\b|\bpanchayat\b": "rural",
    r"\burban\b|\bcity\b|\btown\b|\bmetro\b|\bmunicipal\b|\bnagar\b": "urban",
}

# Marital / family
MARITAL_PATTERNS = {
    r"\bwidow\b|\bvidhwa\b": "widow",
    r"\bsingle\s+mother\b|\bsingle\s+parent\b": "single parent",
    r"\bpregnant\b|\bmaternity\b|\bgarbhvati\b|\bexpecting\b": "pregnant",
    r"\borphan\b|\banath\b": "orphan",
}

# Required context fields before recommending
CONTEXT_FIELDS = ["state", "occupation", "gender", "age", "caste_category"]
MIN_CONTEXT_FOR_RECOMMENDATION = 3


def extract_context_from_text(text: str) -> Dict[str, str]:
    """Extract every possible user attribute from a single message."""
    ctx: Dict[str, str] = {}
    t = text.lower()

    # --- State ---
    for state in sorted(INDIAN_STATES, key=len, reverse=True):
        if state in t:
            ctx["state"] = STATE_DISPLAY.get(state, state.title())
            break

    # --- Occupation ---
    for pattern, occ in OCCUPATIONS.items():
        if re.search(pattern, t, re.I):
            ctx["occupation"] = occ
            break

    # --- Gender ---
    for pattern, g in GENDERS.items():
        if re.search(pattern, t, re.I):
            ctx["gender"] = g
            break

    # --- Caste / category ---
    for pattern, cat in CATEGORIES.items():
        if re.search(pattern, t, re.I):
            ctx["caste_category"] = cat
            break

    # --- Age ---
    for pat in [
        r"\b(\d{1,2})\s*(?:years?|yrs?|year)?\s*old\b",
        r"\bage\s*(?:is\s*)?(\d{1,2})\b",
        r"\bi(?:'?m| am)\s*(\d{1,2})\b",
    ]:
        m = re.search(pat, t, re.I)
        if m:
            age = int(m.group(1))
            if 5 <= age <= 100:
                ctx["age"] = str(age)
            break

    # --- Income ---
    m = re.search(
        r"(?:income|earn|salary|annual\s+income).{0,25}?([\d,.]+)\s*(?:lakh|lac|lpa|per\s*(?:annum|year|month)|/\s*(?:year|month|annum))",
        t, re.I,
    )
    if m:
        ctx["income"] = m.group(0).strip()

    # --- Education level ---
    for pat in EDUCATION_HIGHER_PATTERNS:
        if re.search(pat, t, re.I):
            ctx["education_level"] = "higher"
            break
    if "education_level" not in ctx:
        for pat in EDUCATION_SCHOOL_PATTERNS:
            if re.search(pat, t, re.I):
                ctx["education_level"] = "school"
                break

    # --- BPL / EWS ---
    for pat in BPL_PATTERNS:
        if re.search(pat, t, re.I):
            ctx["bpl"] = "yes"
            break

    # --- Disability ---
    for pat in DISABILITY_PATTERNS:
        if re.search(pat, t, re.I):
            ctx["disability"] = "yes"
            break

    # --- Rural / Urban ---
    for pat, val in RESIDENCE_PATTERNS.items():
        if re.search(pat, t, re.I):
            ctx["residence"] = val
            break

    # --- Marital / special family status ---
    for pat, val in MARITAL_PATTERNS.items():
        if re.search(pat, t, re.I):
            ctx["family_status"] = val
            break

    # --- Negations ---
    for pattern, cat in CATEGORIES.items():
        neg = re.search(r"(?:not|no|neither|don'?t|isn'?t|i'?m not)\s+(?:a\s+)?" + pattern, t, re.I)
        if neg and ctx.get("caste_category") == cat:
            del ctx["caste_category"]

    neg_dis = re.search(r"(?:not|no|don'?t have)\s+(?:a\s+)?(?:disabl|handicap|pwd|divyang)", t, re.I)
    if neg_dis and "disability" in ctx:
        del ctx["disability"]

    neg_bpl = re.search(r"(?:not|no)\s+(?:bpl|below poverty|ews|poor|economically weak)", t, re.I)
    if neg_bpl and "bpl" in ctx:
        del ctx["bpl"]

    return ctx


def build_cumulative_context(
    history: Optional[List[Any]],
    current_message: str,
) -> Dict[str, str]:
    """Walk entire conversation building user context. Later messages override."""
    ctx: Dict[str, str] = {}
    for msg in (history or []):
        role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
        content = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
        if role == "user" and content:
            ctx.update(extract_context_from_text(content))
    ctx.update(extract_context_from_text(current_message))
    return ctx


def context_completeness(ctx: Dict[str, str]) -> int:
    return sum(1 for f in CONTEXT_FIELDS if ctx.get(f))


def missing_context_fields(ctx: Dict[str, str]) -> List[str]:
    return [f for f in CONTEXT_FIELDS if not ctx.get(f)]


# ============================================================
# 2. MULTI-DIMENSIONAL SCHEME FILTER
#    Each filter returns True = keep, False = reject.
#    Runs every filter in sequence on each candidate.
# ============================================================

def _get_elig(scheme: dict) -> dict:
    """Safely extract eligibility_criteria dict."""
    elig = scheme.get("eligibility_criteria") or {}
    return elig if isinstance(elig, dict) else {}


def _scheme_text(scheme: dict) -> str:
    """Combine name + brief + eligibility text for keyword searching."""
    name = (scheme.get("scheme_name") or "")
    brief = (scheme.get("brief_description") or "")
    elig = _get_elig(scheme)
    raw = (elig.get("raw_eligibility_text") or "")
    return f"{name} {brief} {raw}".lower()


# --- Filter: State ---
def _filter_state(scheme: dict, user_state: str) -> bool:
    elig = _get_elig(scheme)
    scheme_state = (elig.get("state") or "").strip().lower()
    if not scheme_state or scheme_state in ("all india", "any", "all", "nationwide"):
        return True
    # "All India (..." or state contains user_state
    if "all india" in scheme_state:
        return True
    user_lower = user_state.strip().lower()
    return user_lower in scheme_state or scheme_state in user_lower


# --- Filter: Gender ---
def _filter_gender(scheme: dict, user_gender: str) -> bool:
    elig = _get_elig(scheme)
    sg = (elig.get("gender") or "any").strip().lower()
    if sg in ("any", ""):
        return True
    ug = user_gender.lower()
    # Exact match
    if sg == ug:
        return True
    # Use word boundary check to prevent "male" matching inside "female"
    if re.search(r"\b" + re.escape(ug) + r"\b", sg):
        return True
    return False


# --- Filter: Caste / Category ---
def _filter_caste(scheme: dict, user_caste: str) -> bool:
    elig = _get_elig(scheme)
    sc = (elig.get("caste_category") or "any").strip().lower()
    if sc in ("any", ""):
        return True
    uc = user_caste.lower()
    # "any (higher subsidy for SC/ST)" → keep
    if "any" in sc:
        return True
    # Exact or substring
    if uc in sc or sc in uc:
        return True
    # Handle SC/ST combined: user=SC → scheme SC/ST is OK
    if uc in ("sc", "st") and "sc/st" in sc:
        return True
    if uc == "sc/st" and ("sc" in sc or "st" in sc):
        return True
    # "general" user should NOT see SC/ST/OBC-only schemes
    if uc == "general" and re.search(r"\bsc\b|\bst\b|\bobc\b|\bminority\b", sc):
        return False
    return False


# --- Filter: Age ---
def _parse_age_range(age_str: str) -> Optional[Tuple[int, int]]:
    """Parse age strings like '18-40', '60+', '<10', '18+' etc."""
    s = age_str.strip().lower()
    if not s or s in ("any", "all", "no limit"):
        return None
    m = re.search(r"(\d+)\s*[-–to]+\s*(\d+)", s)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m = re.search(r"(\d+)\s*\+", s)
    if m:
        return (int(m.group(1)), 120)
    m = re.search(r"<\s*(\d+)", s)
    if m:
        return (0, int(m.group(1)))
    m = re.search(r">\s*(\d+)", s)
    if m:
        return (int(m.group(1)), 120)
    return None


def _filter_age(scheme: dict, user_age: int) -> bool:
    elig = _get_elig(scheme)
    age_str = (elig.get("age_range") or "any").strip()
    rng = _parse_age_range(age_str)
    if rng is None:
        return True
    lo, hi = rng
    return lo <= user_age <= hi


# --- Filter: Occupation ---
def _filter_occupation(scheme: dict, user_occupation: str) -> bool:
    elig = _get_elig(scheme)
    so = (elig.get("occupation") or "any").strip().lower()
    if so in ("any", ""):
        return True
    uo = user_occupation.lower()
    # Direct match
    if uo in so or so in uo:
        return True
    # Farmer schemes: reject if user is student/entrepreneur/worker
    if "farmer" in so and uo not in ("farmer",):
        return False
    # Student schemes: allow (most student schemes have occ=student or any)
    if "student" in so and uo != "student":
        return False
    # Entrepreneur schemes
    if "entrepreneur" in so and uo not in ("entrepreneur",):
        return False
    # Senior citizen
    if "senior" in so and uo != "senior citizen":
        return False
    return True


# --- Filter: Education level (pre-matric vs post-matric) ---
def _scheme_is_pre_matric(text: str) -> bool:
    if re.search(r"\bpre[- ]?matric\b", text):
        return True
    # Mentions class 1-10 but NOT class 11-12 / college / post-matric
    if re.search(r"\bclass(?:es)?\s+(?:[1-9]|10)\b", text):
        if not re.search(r"\bclass\s*1[1-2]\b|\bpost[- ]?matric\b|\bcollege\b|\buniversity\b|\bdegree\b|\bgraduate\b", text):
            return True
    return False


def _scheme_is_post_matric(text: str) -> bool:
    return bool(re.search(
        r"\bpost[- ]?matric\b|\bcollege\b|\buniversity\b|\bdegree\b|\bgraduate\b"
        r"|\bprofessional\s+course\b|\bengineering\b|\bmbbs\b|\bdiploma\b",
        text,
    ))


def _filter_education(scheme: dict, user_edu: str) -> bool:
    text = _scheme_text(scheme)
    if user_edu == "higher":
        return not _scheme_is_pre_matric(text)
    elif user_edu == "school":
        return not _scheme_is_post_matric(text)
    return True


# --- Filter: Disability ---
def _filter_disability(scheme: dict, user_has_disability: bool) -> bool:
    """If scheme is *only* for disabled people and user is NOT disabled, reject."""
    text = _scheme_text(scheme)
    name = (scheme.get("scheme_name") or "").lower()
    # Schemes with "disability" or "divyang" or "PWD" in the name are disability-specific
    is_disability_scheme = bool(re.search(
        r"\bdisabilit\w+\b|\bdivyang\b|\bpwd\b|\bhandicap\w*\b|\bblind\b|\bdeaf\b",
        name,
    ))
    if is_disability_scheme and not user_has_disability:
        return False
    return True


# --- Filter: Widow / Orphan specific schemes ---
def _filter_family_status(scheme: dict, user_status: Optional[str]) -> bool:
    name = (scheme.get("scheme_name") or "").lower()
    # Widow-only schemes
    if re.search(r"\bwidow\b|\bvidhwa\b", name) and user_status != "widow":
        return False
    # Orphan-only schemes
    if re.search(r"\borphan\b|\banath\b", name) and user_status != "orphan":
        return False
    return True


# --- Filter: Farmer-specific land schemes for non-farmers ---
def _filter_farmer_schemes(scheme: dict, user_occupation: str) -> bool:
    """Don't show crop insurance / Kisan schemes to non-farmers."""
    if user_occupation == "farmer":
        return True
    name = (scheme.get("scheme_name") or "").lower()
    if re.search(r"\bkisan\b|\bcrop\b|\bfasal\b|\bkcc\b|\bmandi\b|\be-?nam\b|\bagriculture\b", name):
        return False
    return True


# --- Filter: Senior citizen schemes for young people ---
def _filter_senior_schemes(scheme: dict, user_age: Optional[int], user_occupation: str) -> bool:
    name = (scheme.get("scheme_name") or "").lower()
    is_senior_scheme = bool(re.search(r"\bold\s*age\b|\bsenior\s*citizen\b|\bvaya\b|\bvridh\b", name))
    if not is_senior_scheme:
        return True
    if user_occupation == "senior citizen":
        return True
    if user_age and user_age >= 55:
        return True
    return False


# --- Filter: Children-only schemes for adults ---
def _filter_child_schemes(scheme: dict, user_age: Optional[int]) -> bool:
    name = (scheme.get("scheme_name") or "").lower()
    brief = (scheme.get("brief_description") or "").lower()
    # Schemes clearly for children (Sukanya, Beti Bachao, child labor, etc.)
    is_child_scheme = bool(re.search(
        r"\bchild\s+labour\b|\bbalika\b|\bbeti\b|\bsukanya\b|\bgirl\s+child\b",
        name,
    ))
    if is_child_scheme and user_age and user_age > 25:
        # Sukanya Samriddhi can be opened by parents, so check brief
        if "parent" in brief or "guardian" in brief:
            return True
        return False
    return True


def filter_schemes_for_user(
    candidates: List[Dict[str, Any]],
    user_ctx: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Run ALL filters. A scheme must pass every applicable filter to survive.
    Logs what was removed and why.
    """
    user_state = user_ctx.get("state")
    user_gender = user_ctx.get("gender")
    user_caste = user_ctx.get("caste_category")
    user_age_str = user_ctx.get("age")
    user_age = int(user_age_str) if user_age_str and user_age_str.isdigit() else None
    user_occupation = user_ctx.get("occupation", "")
    user_edu = user_ctx.get("education_level")
    user_disability = user_ctx.get("disability") == "yes"
    user_family = user_ctx.get("family_status")

    filtered = []
    reasons: Dict[str, int] = {}

    for s in candidates:
        rejected = None

        if user_state and not _filter_state(s, user_state):
            rejected = "state"
        elif user_gender and not _filter_gender(s, user_gender):
            rejected = "gender"
        elif user_caste and not _filter_caste(s, user_caste):
            rejected = "caste"
        elif user_age is not None and not _filter_age(s, user_age):
            rejected = "age"
        elif user_occupation and not _filter_occupation(s, user_occupation):
            rejected = "occupation"
        elif user_edu and not _filter_education(s, user_edu):
            rejected = "education_level"
        elif not _filter_disability(s, user_disability):
            rejected = "disability"
        elif user_family is not None and not _filter_family_status(s, user_family):
            rejected = "family_status"
        elif user_occupation and not _filter_farmer_schemes(s, user_occupation):
            rejected = "farmer_specific"
        elif not _filter_senior_schemes(s, user_age, user_occupation):
            rejected = "senior_specific"
        elif user_age is not None and not _filter_child_schemes(s, user_age):
            rejected = "child_specific"

        if rejected:
            reasons[rejected] = reasons.get(rejected, 0) + 1
        else:
            filtered.append(s)

    if reasons:
        logger.info(
            "Filter results: %d→%d kept. Removed: %s",
            len(candidates), len(filtered),
            ", ".join(f"{k}={v}" for k, v in sorted(reasons.items())),
        )

    return filtered


# ============================================================
# 3. ENDPOINTS
# ============================================================


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Scheme Saathi Backend...")
    logger.info("Gemini model: %s", settings.GEMINI_MODEL)

    # Initialize database schema (creates tables on first run).
    try:
        await init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)

    logger.info("Total schemes: %s", rag_service.get_total_schemes())
    logger.info("Ready to serve requests")


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "message": "Welcome to Scheme Saathi API",
        "docs_url": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    try:
        gemini_ok = gemini_service.check_health()
        rag_ok = rag_service.check_health()
        total = rag_service.get_total_schemes()
        return HealthResponse(
            status="healthy" if (gemini_ok and rag_ok and total) else "degraded",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            gemini_status="connected" if gemini_ok else "disconnected",
            vector_db_status="loaded" if rag_ok else "error",
            total_schemes=total,
            timestamp=datetime.now(),
        )
    except Exception as e:
        logger.exception("Health check failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Health check error: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int | None = Depends(get_current_user_id),
):
    """
    Main chat: extract context → decide gather/recommend → filter → respond.
    """
    query = (request.message or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info("Chat request: %s", query[:100])

    try:
        # 1. Cumulative context from all user messages
        user_ctx = build_cumulative_context(request.conversation_history, query)
        completeness = context_completeness(user_ctx)
        missing = missing_context_fields(user_ctx)

        logger.info(
            "Context: %s | completeness=%d/%d | missing=%s",
            user_ctx, completeness, len(CONTEXT_FIELDS), missing,
        )

        # 2. Decide
        ready = completeness >= MIN_CONTEXT_FOR_RECOMMENDATION
        candidates: List[Dict[str, Any]] = []

        if ready:
            # Build rich search query
            search_parts = [query]
            for key in ("occupation", "state", "gender", "caste_category", "education_level"):
                if user_ctx.get(key):
                    search_parts.append(user_ctx[key])
            if user_ctx.get("disability") == "yes":
                search_parts.append("disability divyang PWD")
            if user_ctx.get("bpl") == "yes":
                search_parts.append("BPL below poverty economically weaker")

            # Add recent user messages for semantic richness
            if request.conversation_history:
                for m in request.conversation_history[-4:]:
                    role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
                    content = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
                    if role == "user" and content:
                        search_parts.append(content)

            search_query = " ".join(search_parts)

            # RAG search (fetch extra, filter will trim)
            raw = rag_service.search_schemes(
                query=search_query,
                user_context=user_ctx,
                top_k=settings.TOP_K_SCHEMES * 3,
            )
            logger.info("RAG returned %d candidates", len(raw))

            # HARD FILTER: multi-dimensional
            candidates = filter_schemes_for_user(raw, user_ctx)
            logger.info("After filter: %d candidates", len(candidates))

            candidates = candidates[:settings.TOP_K_SCHEMES]

        # 3. Gemini response
        reply = gemini_service.chat(
            user_message=query,
            conversation_history=request.conversation_history,
            matched_schemes=candidates if ready else None,
            user_context=user_ctx,
            missing_fields=missing,
            language=request.language,
        )
        persistent_chat_id: int | None = None

        # 4. Persist conversation to DB when user is authenticated
        # (Supabase JWT present). WhatsApp / anonymous calls skip this.
        if user_id is not None:
            logger.info("Authenticated user_id=%s; persisting chat to DB.", user_id)
            try:
                chat_obj, _history = await get_or_create_chat_for_message(
                    db,
                    user_id=user_id,
                    chat_id=request.chat_id,
                )
                if chat_obj:
                    persistent_chat_id = chat_obj.id
                    await append_message(db, chat_obj.id, user_id, "user", query)
                    await append_message(db, chat_obj.id, user_id, "assistant", reply)
                    logger.info("Saved chat_id=%s with 2 messages for user_id=%s", chat_obj.id, user_id)
                else:
                    logger.warning("get_or_create_chat_for_message returned None for user_id=%s", user_id)
            except Exception as db_err:
                logger.exception("Failed to persist chat to DB: %s", db_err)
                # Don't fail the request; the AI reply was already generated.
        else:
            logger.debug("Anonymous request; skipping DB persistence.")

        return ChatResponse(
            message=reply,
            chat_id=persistent_chat_id,
            schemes=candidates[:5] if ready else [],
            needs_more_info=not ready,
            extracted_context=user_ctx if user_ctx else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.get("/schemes")
async def list_schemes(
    category: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 20,
):
    try:
        schemes: List[Dict[str, Any]] = list(rag_service.schemes)
        if category:
            cat_lower = category.strip().lower()
            schemes = [s for s in schemes if (s.get("category") or "").lower() == cat_lower]
        if state:
            schemes = [s for s in schemes if _filter_state(s, state)]
        return {"total": len(schemes[:limit]), "schemes": schemes[:limit]}
    except Exception as e:
        logger.exception("List schemes failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schemes/categories")
async def list_categories():
    return {"categories": rag_service.get_categories()}


@app.get("/schemes/{scheme_id}")
async def get_scheme(scheme_id: str):
    try:
        scheme = rag_service.get_scheme_by_id(scheme_id)
        if scheme is None:
            raise HTTPException(status_code=404, detail="Scheme not found")
        return scheme
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Get scheme failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SchemeSearchResponse)
async def search_schemes(request: SchemeSearchRequest):
    query = (request.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    user_ctx: Dict[str, Any] = {}
    if request.state:
        user_ctx["state"] = request.state
    if request.category:
        user_ctx["category"] = request.category

    results = rag_service.search_schemes(
        query=query,
        user_context=user_ctx if user_ctx else None,
        top_k=request.top_k or settings.TOP_K_SCHEMES,
    )
    results = filter_schemes_for_user(results, user_ctx)

    return SchemeSearchResponse(
        query=query,
        total_matches=len(results),
        schemes=results,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
