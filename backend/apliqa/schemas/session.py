import uuid
from typing import TypedDict

from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    job_id: uuid.UUID


class SessionMessageRequest(BaseModel):
    message: str


class SessionCreateResponse(BaseModel):
    session_id: uuid.UUID
    question: str
    gaps_total: int
    gaps_remaining: int


class SessionMessageResponse(BaseModel):
    complete: bool
    question: str | None = None
    gaps_remaining: int | None = None


# Internal state stored in JSONB — not exposed via API
class InterviewState(TypedDict):
    job_id: str
    gap_analysis_id: str
    profile_id: str
    critical_gaps: list[str]  # ordered: Category C first, then Category B
    gap_categories: dict  # {gap_str: "B" | "C"} — used by QuestionGenerator
    addressed_gaps: list[str]
    current_gap_index: int
    current_question: str
    messages: list[dict]  # {"role": "assistant"|"user", "content": "..."}
