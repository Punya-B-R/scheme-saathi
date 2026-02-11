"""
FastAPI application for Scheme Saathi backend.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
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
from app.services.gemini_service import gemini_service
from app.services.rag_service import rag_service

# Configure logging before app creation
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


# ============================================================
# Lightweight context extraction (regex-based, no API call)
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

# Canonical name mapping for display
STATE_DISPLAY = {s: s.title() for s in INDIAN_STATES}
STATE_DISPLAY["delhi"] = "Delhi"
STATE_DISPLAY["tamil nadu"] = "Tamil Nadu"
STATE_DISPLAY["uttar pradesh"] = "Uttar Pradesh"
STATE_DISPLAY["madhya pradesh"] = "Madhya Pradesh"
STATE_DISPLAY["andhra pradesh"] = "Andhra Pradesh"
STATE_DISPLAY["himachal pradesh"] = "Himachal Pradesh"
STATE_DISPLAY["arunachal pradesh"] = "Arunachal Pradesh"
STATE_DISPLAY["west bengal"] = "West Bengal"
STATE_DISPLAY["jammu and kashmir"] = "Jammu and Kashmir"

OCCUPATIONS = {
    r"\bfarmer\b|\bkisan\b|\bfarming\b|\bagriculture\b|\bcrop\b|\bkhet\b": "farmer",
    r"\bstudents?\b|\bstudying\b|\bcollege\b|\buniversity\b|\bengineering\b|\bmedical\s+student\b|\bbtech\b|\bmba\b|\bschool\b|\bscholarship\b|\bclass\s+\d|\bmatric\b|\bdegree\b|\bpost.?graduate\b|\bgraduate\b|\bdiploma\b": "student",
    r"\bsenior\s*citizens?\b|\bretired\b|\bold\s*age\b|\bpensioners?\b|\belderly\b|\bvridh\b|\bpension\b": "senior citizen",
    r"\bbusiness\b|\bentrepreneur\b|\bself.?employed\b|\bshop\b|\bstartup\b|\bmsme\b|\btrader\b|\budyami\b": "entrepreneur",
    r"\bworker\b|\blabou?r\b|\bemployee\b|\bdaily\s*wage\b|\bsalaried\b|\bjob\b": "worker",
    r"\bfisherm[ae]n\b|\bfishing\b": "fisherman",
    r"\bartisan\b|\bhandicraft\b|\bweaver\b|\bpotter\b|\bvishwakarma\b": "artisan",
}

GENDERS = {
    r"\bfemale\b|\bwoman\b|\bwomen\b|\bgirl\b|\bmahila\b|\bmother\b|\bpregnant\b|\bwidow\b|\blady\b|\bdaughter\b|\bsister\b": "female",
    r"\bmale\b(?!\s*(?:and|or|\/)\s*female)|\bboy\b": "male",
}

CATEGORIES = {
    r"\bsc\s*/\s*st\b|\bsc\s+st\b|\bsc\s*&\s*st\b|\bsc\s+and\s+st\b": "SC/ST",
    r"\bsc\b|\bschedul\w+\s*caste\b|\bdalit\b": "SC",
    r"\bst\b|\bschedul\w+\s*tribe\b|\btribal\b|\badivasi\b": "ST",
    r"\bobc\b|\bother\s*backward\b": "OBC",
    r"\bgeneral\s*category\b|\bunreserved\b": "General",
    r"\bminority\b|\bmuslim\b|\bchristian\b|\bsikh\b|\bbuddhist\b|\bjain\b|\bparsi\b": "Minority",
}

# Education-level keywords
# "higher" = post-matric / college / university / professional
# "school"  = pre-matric (class 1-10)
EDUCATION_LEVELS = {
    "higher": [
        r"\bengineering\b", r"\bbtech\b", r"\bb\.?tech\b", r"\bb\.?e\b",
        r"\bmtech\b", r"\bm\.?tech\b", r"\bmba\b", r"\bbba\b", r"\bm\.?sc\b",
        r"\bb\.?sc\b", r"\bm\.?a\b", r"\bb\.?a\b", r"\bm\.?com\b", r"\bb\.?com\b",
        r"\bph\.?d\b", r"\bpost.?graduate\b", r"\bgraduate\b", r"\bdiploma\b",
        r"\bcollege\b", r"\buniversity\b", r"\bdegree\b", r"\bprofessional\s+course\b",
        r"\bmedical\s+student\b", r"\bmbbs\b", r"\blaw\b", r"\bllb\b",
        r"\bnursing\b", r"\bpolytechnic\b", r"\biti\b", r"\bpost.?matric\b",
        r"\bclass\s*1[1-2]\b", r"\b1[1-2]th\b", r"\bhigher\s+secondary\b",
        r"\bhigher\s+education\b", r"\bunder.?graduate\b", r"\bug\b", r"\bpg\b",
    ],
    "school": [
        r"\bpre.?matric\b", r"\bclass\s*[1-9]\b(?!\d)", r"\bclass\s*10\b",
        r"\b[1-9]th\s+(?:class|standard|std)\b", r"\b10th\s+(?:class|standard|std)\b",
        r"\bprimary\s+school\b", r"\bmiddle\s+school\b", r"\bhigh\s+school\b",
    ],
}

# Required context fields and how many we need before recommending
CONTEXT_FIELDS = ["state", "occupation", "gender", "age", "caste_category"]
MIN_CONTEXT_FOR_RECOMMENDATION = 3  # need at least 3 of 5 to recommend


def extract_context_from_text(text: str) -> Dict[str, str]:
    """Extract user context from a message using regex. Fast, no API call."""
    ctx: Dict[str, str] = {}
    t = text.lower()

    # State
    for state in INDIAN_STATES:
        if state in t:
            ctx["state"] = STATE_DISPLAY.get(state, state.title())
            break

    # Occupation
    for pattern, occ in OCCUPATIONS.items():
        if re.search(pattern, t, re.I):
            ctx["occupation"] = occ
            break

    # Gender
    for pattern, g in GENDERS.items():
        if re.search(pattern, t, re.I):
            ctx["gender"] = g
            break

    # Caste/category
    for pattern, cat in CATEGORIES.items():
        if re.search(pattern, t, re.I):
            ctx["caste_category"] = cat
            break

    # Age
    age_match = re.search(r"\b(\d{1,2})\s*(?:years?|yrs?|year)?\s*old\b", t, re.I)
    if not age_match:
        age_match = re.search(r"\bage\s*(?:is\s*)?(\d{1,2})\b", t, re.I)
    if not age_match:
        age_match = re.search(r"\bi(?:'?m| am)\s*(\d{1,2})\b", t, re.I)
    if age_match:
        age = int(age_match.group(1))
        if 5 <= age <= 100:
            ctx["age"] = str(age)

    # Income
    income_match = re.search(r"(?:income|earn|salary).{0,20}?([\d,.]+)\s*(?:lakh|lac|lpa|per\s*(?:annum|year|month))", t, re.I)
    if income_match:
        ctx["income"] = income_match.group(0).strip()

    # Education level  (higher = post-matric / college+, school = pre-matric)
    for level, patterns in EDUCATION_LEVELS.items():
        for pat in patterns:
            if re.search(pat, t, re.I):
                ctx["education_level"] = level
                break
        if "education_level" in ctx:
            break

    # Negations: "not SC", "not minority", "I'm not OBC"
    for pattern, cat in CATEGORIES.items():
        neg = re.search(r"(?:not|no|neither|don'?t|isn'?t|i'?m not)\s+(?:a\s+)?" + pattern, t, re.I)
        if neg and "caste_category" in ctx and ctx["caste_category"] == cat:
            del ctx["caste_category"]

    return ctx


def build_cumulative_context(
    history: Optional[List[Any]],
    current_message: str,
) -> Dict[str, str]:
    """
    Walk through entire conversation and build up user context.
    Later messages override earlier ones (user corrects themselves).
    """
    ctx: Dict[str, str] = {}

    # Process history
    for msg in (history or []):
        role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
        content = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
        if role == "user" and content:
            extracted = extract_context_from_text(content)
            ctx.update(extracted)

    # Process current message (highest priority)
    current_ctx = extract_context_from_text(current_message)
    ctx.update(current_ctx)

    return ctx


def context_completeness(ctx: Dict[str, str]) -> int:
    """Count how many context fields we have."""
    return sum(1 for field in CONTEXT_FIELDS if ctx.get(field))


def missing_context_fields(ctx: Dict[str, str]) -> List[str]:
    """Return which important fields are still missing."""
    return [f for f in CONTEXT_FIELDS if not ctx.get(f)]


# ============================================================
# Hard state filtering
# ============================================================

def scheme_matches_state(scheme: dict, user_state: str) -> bool:
    """
    STRICT state filter. A scheme matches if:
    - Its state is "All India" / empty / not specified
    - Its state exactly matches the user's state
    Returns False for schemes from OTHER specific states.
    """
    elig = scheme.get("eligibility_criteria") or {}
    if not isinstance(elig, dict):
        return True

    scheme_state = (elig.get("state") or "").strip().lower()

    # No state specified or All India -> always matches
    if not scheme_state or scheme_state in ("all india", "any", "all", "nationwide"):
        return True

    # Check if user's state is mentioned in the scheme's state
    user_lower = user_state.strip().lower()
    if user_lower in scheme_state or scheme_state in user_lower:
        return True

    # Scheme is for a different specific state -> reject
    return False


def _scheme_is_pre_matric(scheme: dict) -> bool:
    """
    Detect if a scheme is meant for pre-matric students (class 1-10).
    Checks scheme name, description, and eligibility text.
    """
    name = (scheme.get("scheme_name") or "").lower()
    brief = (scheme.get("brief_description") or "").lower()
    elig = scheme.get("eligibility_criteria") or {}
    elig_text = ""
    if isinstance(elig, dict):
        elig_text = (elig.get("raw_eligibility_text") or "").lower()

    combined = f"{name} {brief} {elig_text}"

    # Explicit pre-matric indicators
    if re.search(r"\bpre[- ]?matric\b", combined):
        return True
    # "class 1 to 10", "class 6 to 10", "studying in class 8/9/10 only"
    if re.search(r"\bclass(?:es)?\s+(?:[1-9]|10)\b", combined) and not re.search(r"\bclass\s*1[1-2]\b|\bpost[- ]?matric\b|\bcollege\b|\buniversity\b|\bdegree\b|\bgraduate\b", combined):
        return True

    return False


def _scheme_is_post_matric(scheme: dict) -> bool:
    """
    Detect if a scheme is explicitly for post-matric / higher-ed students.
    """
    name = (scheme.get("scheme_name") or "").lower()
    brief = (scheme.get("brief_description") or "").lower()
    elig = scheme.get("eligibility_criteria") or {}
    elig_text = ""
    if isinstance(elig, dict):
        elig_text = (elig.get("raw_eligibility_text") or "").lower()

    combined = f"{name} {brief} {elig_text}"

    if re.search(r"\bpost[- ]?matric\b|\bcollege\b|\buniversity\b|\bdegree\b|\bgraduate\b|\bprofessional\s+course\b|\bengineering\b|\bmbbs\b|\bdiploma\b", combined):
        return True
    return False


def filter_schemes_for_user(
    candidates: List[Dict[str, Any]],
    user_ctx: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Hard-filter RAG results based on extracted context.
    This is the critical step that prevents wrong state/gender/education matches.
    """
    filtered = list(candidates)

    # State filter (most important)
    if user_ctx.get("state"):
        filtered = [s for s in filtered if scheme_matches_state(s, user_ctx["state"])]

    # Gender filter
    if user_ctx.get("gender"):
        user_gender = user_ctx["gender"].lower()
        result = []
        for s in filtered:
            elig = s.get("eligibility_criteria") or {}
            if not isinstance(elig, dict):
                result.append(s)
                continue
            scheme_gender = (elig.get("gender") or "any").lower()
            # Keep if scheme is for "any" gender or matches user's gender
            if scheme_gender in ("any", "", user_gender):
                result.append(s)
            # Also keep if scheme is specifically for the user's gender
            elif user_gender in scheme_gender:
                result.append(s)
        filtered = result

    # Education level filter
    edu_level = user_ctx.get("education_level")
    if edu_level == "higher":
        # User is in college / engineering / post-matric → remove pre-matric-only schemes
        before = len(filtered)
        filtered = [s for s in filtered if not _scheme_is_pre_matric(s)]
        removed = before - len(filtered)
        if removed:
            logger.info("Education filter: removed %d pre-matric schemes (user is higher-ed)", removed)
    elif edu_level == "school":
        # User is in school (pre-matric) → remove post-matric-only schemes
        before = len(filtered)
        filtered = [s for s in filtered if not _scheme_is_post_matric(s)]
        removed = before - len(filtered)
        if removed:
            logger.info("Education filter: removed %d post-matric schemes (user is school student)", removed)

    return filtered


# ============================================================
# Endpoints
# ============================================================


@app.on_event("startup")
async def startup_event():
    """Log startup info."""
    logger.info("Starting Scheme Saathi Backend...")
    logger.info("Gemini model: %s", settings.GEMINI_MODEL)
    logger.info("Total schemes: %s", rag_service.get_total_schemes())
    logger.info("Ready to serve requests")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "message": "Welcome to Scheme Saathi API",
        "docs_url": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check: Gemini, vector DB, and scheme count."""
    try:
        gemini_ok = gemini_service.check_health()
        rag_ok = rag_service.check_health()
        total = rag_service.get_total_schemes()
        gemini_status = "connected" if gemini_ok else "disconnected"
        vector_db_status = "loaded" if rag_ok else "error"
        status = "healthy" if (gemini_ok and rag_ok and total) else "degraded"
        return HealthResponse(
            status=status,
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            gemini_status=gemini_status,
            vector_db_status=vector_db_status,
            total_schemes=total,
            timestamp=datetime.now(),
        )
    except Exception as e:
        logger.exception("Health check failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Health check error: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with smart conversation flow:
    1. Extract context from ALL messages (regex, no API call)
    2. If not enough context -> tell Gemini to ask more questions (no schemes passed)
    3. If enough context -> RAG search + hard filter + Gemini response with schemes
    """
    query = (request.message or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info("Chat request: %s", query[:80])

    try:
        # 1. Build cumulative user context from entire conversation
        user_ctx = build_cumulative_context(request.conversation_history, query)
        completeness = context_completeness(user_ctx)
        missing = missing_context_fields(user_ctx)

        logger.info(
            "User context: %s (completeness=%d/%d, missing=%s, edu=%s)",
            user_ctx, completeness, len(CONTEXT_FIELDS), missing,
            user_ctx.get("education_level", "unknown"),
        )

        # 2. Decide: gather more info or recommend?
        ready_to_recommend = completeness >= MIN_CONTEXT_FOR_RECOMMENDATION

        candidates: List[Dict[str, Any]] = []

        if ready_to_recommend:
            # Build enriched search query from context
            search_parts = [query]
            if user_ctx.get("occupation"):
                search_parts.append(user_ctx["occupation"])
            if user_ctx.get("state"):
                search_parts.append(user_ctx["state"])
            if user_ctx.get("gender"):
                search_parts.append(user_ctx["gender"])
            if user_ctx.get("caste_category"):
                search_parts.append(user_ctx["caste_category"])

            # Include recent user messages for better semantic search
            if request.conversation_history:
                recent_user_msgs = [
                    (getattr(m, "content", "") or (m.get("content", "") if isinstance(m, dict) else ""))
                    for m in request.conversation_history[-4:]
                    if (getattr(m, "role", "") or (m.get("role", "") if isinstance(m, dict) else "")) == "user"
                ]
                search_parts.extend(recent_user_msgs)

            search_query = " ".join(search_parts)

            # RAG search
            raw_candidates = rag_service.search_schemes(
                query=search_query,
                user_context=user_ctx,
                top_k=settings.TOP_K_SCHEMES * 2,  # fetch more, filter down
            )
            logger.info("RAG returned %d candidates", len(raw_candidates))

            # HARD FILTER: state, gender, etc.
            candidates = filter_schemes_for_user(raw_candidates, user_ctx)
            logger.info("After hard filter: %d candidates", len(candidates))

            # Cap to top_k
            candidates = candidates[: settings.TOP_K_SCHEMES]

        # 3. Generate AI response
        reply = gemini_service.chat(
            user_message=query,
            conversation_history=request.conversation_history,
            matched_schemes=candidates if ready_to_recommend else None,
            user_context=user_ctx,
            missing_fields=missing,
            language=request.language,
        )

        return ChatResponse(
            message=reply,
            schemes=candidates[:5] if ready_to_recommend else [],
            needs_more_info=not ready_to_recommend,
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
    """List schemes with optional filters."""
    try:
        schemes: List[Dict[str, Any]] = list(rag_service.schemes)
        if category:
            cat_lower = category.strip().lower()
            schemes = [s for s in schemes if (s.get("category") or "").lower() == cat_lower]
        if state:
            schemes = [s for s in schemes if scheme_matches_state(s, state)]
        schemes = schemes[:limit]
        return {"total": len(schemes), "schemes": schemes}
    except Exception as e:
        logger.exception("List schemes failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schemes/categories")
async def list_categories():
    """Return list of unique scheme categories."""
    return {"categories": rag_service.get_categories()}


@app.get("/schemes/{scheme_id}")
async def get_scheme(scheme_id: str):
    """Get a single scheme by ID."""
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
    """Semantic search over schemes with optional filters."""
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

    # Hard filter
    if request.state:
        results = [s for s in results if scheme_matches_state(s, request.state)]
    if request.category:
        results = [
            s for s in results
            if (s.get("category") or "").lower() == (request.category or "").lower()
        ]

    return SchemeSearchResponse(
        query=query,
        total_matches=len(results),
        schemes=results,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
