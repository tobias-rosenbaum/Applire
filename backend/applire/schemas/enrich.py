import uuid
from typing import Literal

from pydantic import BaseModel


class EnrichStartRequest(BaseModel):
    # None = full profile scan
    # "work_experience:<company>:<role>" = scoped to one entry
    scope: str | None = None


class GapItem(BaseModel):
    id: str   # gap descriptor string, e.g. "achievements: Product Lead @ Beta GmbH"
    label: str
    status: Literal["pending", "active", "done", "na", "skipped"]


class EnrichStartResponse(BaseModel):
    session_id: uuid.UUID
    first_question: str
    gaps: list[GapItem]
    estimated_questions: int


class EnrichRespondRequest(BaseModel):
    answer: str


class EnrichRespondResponse(BaseModel):
    next_question: str | None
    gaps: list[GapItem]
    done: bool
    profile_updated: bool


class EnrichActionResponse(BaseModel):
    """Returned by /skip and /na endpoints."""
    next_question: str | None
    gaps: list[GapItem]
    done: bool
