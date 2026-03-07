import uuid
from datetime import datetime

from pydantic import BaseModel


class CVGenerateRequest(BaseModel):
    job_id: uuid.UUID


class CVGenerateResponse(BaseModel):
    cv_id: uuid.UUID
    html_url: str
    pdf_url: str


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
