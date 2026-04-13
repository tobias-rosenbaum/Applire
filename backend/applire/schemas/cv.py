import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator

from applire.models.cv import CVGenerationStatus

CVTemplate = Literal[
    "classic_german",
    "modern_swiss",
    "executive",
    "tech_developer",
    "creative_sidebar",
    "academic",
    "compact_pro",
]


class CVGenerateRequest(BaseModel):
    job_id: uuid.UUID
    template: CVTemplate = "classic_german"


class CVGenerateResponse(BaseModel):
    """Returned immediately by POST /api/cv/generate (async path)."""
    cv_id: uuid.UUID
    status: CVGenerationStatus
    html_url: str  # stable URL — usable once status='ready'
    pdf_url: str
    expires_at: datetime


class CVStatusResponse(BaseModel):
    """Returned by GET /api/cv/{cv_id}/status."""
    cv_id: uuid.UUID
    status: CVGenerationStatus
    html_url: Optional[str] = None
    pdf_url: Optional[str] = None
    error_message: Optional[str] = None
    expires_at: datetime

    model_config = {"from_attributes": True}


def _coerce_none_str(cls, v):
    """Coerce None to empty string for CV tailoring string fields."""
    return v if v is not None else ""


class TailoredWorkEntry(BaseModel):
    company: str = ""
    role: str = ""
    start_date: str = ""
    end_date: str | None = None
    bullets: list[str] = []

    _coerce_fields = field_validator("company", "role", "start_date", mode="before")(_coerce_none_str)


class TailoredEducationEntry(BaseModel):
    institution: str = ""
    degree: str = ""
    field: str = ""
    start_date: str = ""
    end_date: str | None = None

    _coerce_fields = field_validator("institution", "degree", "field", "start_date", mode="before")(_coerce_none_str)


class TailoredLanguage(BaseModel):
    language: str = ""
    level: str = ""

    _coerce_fields = field_validator("language", "level", mode="before")(_coerce_none_str)


class TailoredContact(BaseModel):
    name: str = ""
    email: str | None = None
    phone: str | None = None
    location: str = ""
    linkedin: str | None = None
    photo_url: str | None = None  # ADR-021; file path resolved to base64 URI at render time

    _coerce_fields = field_validator("name", "location", mode="before")(_coerce_none_str)


class TailoredCVData(BaseModel):
    contact: TailoredContact
    summary: str = ""
    work_history: list[TailoredWorkEntry] = []
    skills: list[str] = []
    education: list[TailoredEducationEntry] = []
    languages: list[TailoredLanguage] = []
    show_photo: bool = True  # country-aware photo rendering hook (ADR-021); True for all DACH jobs


class GeneratedCVResponse(BaseModel):
    id: uuid.UUID
    job_analysis_id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}
