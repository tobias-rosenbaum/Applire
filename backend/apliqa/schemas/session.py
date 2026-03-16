import uuid
from datetime import datetime
from typing import Literal, TypedDict

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class SessionCreateRequest(BaseModel):
    job_id: uuid.UUID
    # None = auto-detect based on profile completeness_score vs MODE_B_COMPLETENESS_THRESHOLD
    mode: Literal["targeted", "guided"] | None = None


class SessionMessageRequest(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SessionCreateResponse(BaseModel):
    session_id: uuid.UUID
    mode: Literal["targeted", "guided"]
    first_question: str
    estimated_questions: int  # soft target mid-point for the resolved mode
    # Legacy fields kept for backwards compatibility
    question: str  # same as first_question
    gaps_total: int
    gaps_remaining: int
    resumed: bool = False  # True if an existing active session was returned


class SessionMessageResponse(BaseModel):
    complete: bool
    question: str | None = None
    gaps_remaining: int | None = None
    # Populated when complete=True
    reason: Literal["gaps_resolved", "user_ended", "max_questions_reached"] | None = None
    questions_asked: int | None = None
    gaps_resolved: int | None = None
    gaps_unresolved: list[str] | None = None
    completeness_score: float | None = None


class SessionStateResponse(BaseModel):
    """Returned by GET /api/session/{id} — used for agent recovery and pause/resume."""

    session_id: uuid.UUID
    job_id: uuid.UUID
    mode: Literal["targeted", "guided"]
    status: Literal["active", "complete", "expired"]
    questions_asked: int
    hard_ceiling: int
    current_question: str | None  # None if session is complete
    gaps_remaining: int
    completeness_score: float
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None


# ---------------------------------------------------------------------------
# Internal state stored in JSONB — not exposed via API
# ---------------------------------------------------------------------------


class InterviewState(TypedDict):
    mode: str  # "targeted" | "guided"
    job_id: str
    gap_analysis_id: str | None  # None for MODE B until lazy analysis
    profile_id: str
    # MODE A: ordered gap strings (C-first, then B)
    # MODE B: ordered section names to build
    critical_gaps: list[str]
    gap_categories: dict  # {gap_str: "B" | "C"} — empty dict for MODE B
    addressed_gaps: list[str]
    current_gap_index: int
    current_question: str
    messages: list[dict]  # {"role": "assistant"|"user", "content": "..."}
    questions_asked: int
    hard_ceiling: int
