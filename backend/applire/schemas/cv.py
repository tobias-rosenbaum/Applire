import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from applire.models.cv import CVGenerationStatus

CVTemplate = Literal["classic_german", "modern_swiss"]


class CVGenerateRequest(BaseModel):
    job_id: uuid.UUID
    template: CVTemplate = "classic_german"


class CVGenerateResponse(BaseModel):
    """Returned immediately by POST /api/cv/generate (async path)."""
    cv_id: uuid.UUID
    status: CVGenerationStatus
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


class TailoredWorkEntry(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: str | None = None
    bullets: list[str] = []


class TailoredEducationEntry(BaseModel):
    institution: str
    degree: str
    field: str = ""
    start_date: str = ""
    end_date: str | None = None


class TailoredLanguage(BaseModel):
    language: str
    level: str


class TailoredContact(BaseModel):
    name: str = ""
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None


class TailoredCVData(BaseModel):
    contact: TailoredContact
    summary: str = ""
    work_history: list[TailoredWorkEntry] = []
    skills: list[str] = []
    education: list[TailoredEducationEntry] = []
    languages: list[TailoredLanguage] = []


class GeneratedCVResponse(BaseModel):
    id: uuid.UUID
    job_analysis_id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}
