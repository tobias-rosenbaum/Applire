# backend/applire/schemas/cv_sections.py
"""Pydantic schemas for the CV Section Editor API (Sprint 9, ADR-019)."""
import uuid
from typing import Optional

from pydantic import BaseModel, Field


class SnapshotPosition(BaseModel):
    """One work history entry as stored in content_snapshot."""
    id: str  # stable UUID string assigned at snapshot time
    index: int  # index in tailored_data.work_history — used for override application
    title: str
    company: str
    period: str
    bullets: list[str]


class ContentSnapshot(BaseModel):
    """Structured rendering context captured at CV generation time."""
    introduction: str
    positions: list[SnapshotPosition]
    skills: list[str]


class GapHintItem(BaseModel):
    id: str
    label: str


class SectionItem(BaseModel):
    section_id: str  # e.g. "introduction", "position::uuid", "skills"
    label: str       # Human-readable, e.g. "Introduction", "Senior Engineer — SAP"
    content: str     # Snapshot content merged with override (override wins)
    has_override: bool
    gaps: list[GapHintItem]


class CVSectionsResponse(BaseModel):
    sections: list[SectionItem]
    general_gaps: list[GapHintItem]


class SectionPatchRequest(BaseModel):
    content: str = Field(..., max_length=10_000)
    save_to_profile: bool = False


class SectionPatchResponse(BaseModel):
    html: str
    overrides_applied: list[str]
    resolved_gaps: list[str] = []


class AssistStartRequest(BaseModel):
    gap_id: str


class AssistStartResponse(BaseModel):
    session_id: str
    question: str


class AssistAnswerRequest(BaseModel):
    session_id: str
    answer: str


class AssistAnswerResponse(BaseModel):
    suggestion: str


class RewriteRequest(BaseModel):
    directions: str = Field("", max_length=2000)
    gap_ids: list[str] = Field(default_factory=list)


class RewriteResponse(BaseModel):
    suggestion: str
