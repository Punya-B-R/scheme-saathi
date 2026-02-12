"""
Pydantic models for request/response schemas and scheme data structure.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# CHAT MODELS (for conversation)
# ============================================================


class ChatMessage(BaseModel):
    """Single message in a conversation"""

    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Request to the chat endpoint"""

    message: str = Field(..., description="User's message", min_length=1)
    # Optional chat identifier for persistent history (when authenticated).
    # Frontend can omit this; backend will create a new chat and return chat_id.
    chat_id: Optional[int] = Field(
        default=None,
        description="Optional chat id for persistent history; if omitted, backend may create a new chat.",
    )
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        description="Previous messages in this conversation",
    )
    user_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="User context (state, occupation, etc.) if already known",
    )
    language: str = Field(
        default="en",
        description="Preferred language: 'en' for English, 'hi' for Hindi",
    )


class ChatResponse(BaseModel):
    """Response from the chat endpoint"""

    message: str = Field(..., description="AI assistant's response")
    chat_id: Optional[int] = Field(
        default=None,
        description="Persistent chat id (when user is authenticated).",
    )
    schemes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Matched schemes (if any)",
    )
    needs_more_info: bool = Field(
        default=False,
        description="Whether AI needs more information from user",
    )
    extracted_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Information extracted from conversation",
    )


# ============================================================
# SCHEME MODELS (for scheme data structure)
# ============================================================


class EligibilityCriteria(BaseModel):
    """Eligibility criteria for a scheme"""

    age_range: str
    gender: str
    caste_category: str
    income_limit: str
    occupation: str
    state: str
    district: str = ""
    land_ownership: str = ""
    education: str = ""

    # Boolean flags
    requires_aadhaar: bool = False
    requires_bank_account: bool = False
    bpl_mandatory: bool = False

    # Lists
    other_conditions: List[str] = Field(default_factory=list)
    checklist: List[str] = Field(default_factory=list)

    # Original raw text
    raw_eligibility_text: str = ""


class Benefits(BaseModel):
    """Benefits provided by a scheme"""

    summary: str
    financial_benefit: str = ""
    benefit_type: str = ""
    frequency: str = ""
    additional_benefits: List[str] = Field(default_factory=list)
    raw_benefits_text: str = ""


class Document(BaseModel):
    """Required document"""

    document_name: str
    mandatory: bool = True
    specifications: str = ""
    notes: str = ""
    validity: str = ""


class Scheme(BaseModel):
    """Complete government scheme"""

    # Basic Info
    scheme_id: str
    scheme_name: str
    scheme_name_local: str = ""
    category: str
    brief_description: str
    detailed_description: str = ""

    # Benefits
    benefits: Any = None  # Benefits | dict (flexible for loaded JSON)

    # Eligibility
    eligibility_criteria: Any = None  # EligibilityCriteria | dict

    # Documents & Process
    required_documents: List[Any] = Field(default_factory=list)
    application_process: List[str] = Field(default_factory=list)

    # Links & Contact
    official_website: str = ""
    application_link: str = ""
    helpline_number: str = ""
    helpline_email: str = ""

    # Metadata
    scheme_type: str = ""
    ministry_department: str = ""
    implementing_agency: str = ""
    state: str = "All India"
    geographical_coverage: str = "All India"

    # Source & Quality
    source_url: str = ""
    data_quality_score: int = 0

    # Match score (added during search)
    match_score: Optional[float] = None
    match_reason: Optional[str] = None

    class Config:
        extra = "allow"


# ============================================================
# HEALTH CHECK MODEL
# ============================================================


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="'healthy' or 'degraded'")
    app_name: str
    version: str
    gemini_status: str = Field(..., description="'connected' or 'disconnected'")
    vector_db_status: str = Field(..., description="'loaded' or 'error'")
    total_schemes: int = Field(..., description="Number of schemes loaded")
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================
# LIST SCHEMES MODELS
# ============================================================


class SchemeListResponse(BaseModel):
    """Response for listing schemes"""

    total: int
    schemes: List[Dict[str, Any]]
    filters_applied: Optional[Dict[str, str]] = None


# ============================================================
# SEARCH (for /search endpoint)
# ============================================================


class SchemeSearchRequest(BaseModel):
    """Request for scheme search endpoint"""

    query: str = Field(..., min_length=1)
    category: Optional[str] = None
    state: Optional[str] = None
    top_k: Optional[int] = Field(10, ge=1, le=50)


class SchemeSearchResponse(BaseModel):
    """Response for scheme search endpoint"""

    query: str
    total_matches: int
    schemes: List[Dict[str, Any]] = Field(default_factory=list)
