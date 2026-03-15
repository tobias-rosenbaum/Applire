from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


# ─── Section sub-models ───────────────────────────────────────────────────────

class ProfessionalSummary(BaseModel):
    """Multilingual professional summary — user's elevator pitch."""
    de: str | None = None
    en: str | None = None


class PersonalInfo(BaseModel):
    name: str = ""
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    address: str | None = None
    nationality: str | None = None
    date_of_birth: date | None = None
    photo_url: str | None = None
    linkedin_url: str | None = None
    xing_url: str | None = None
    website_url: str | None = None


# Backwards-compat alias — existing JSONB records and LLM output use 'contact'.
Contact = PersonalInfo


class WorkEntry(BaseModel):
    company: str
    role: str
    location: str | None = None
    # str — LLM returns partial dates like "2020-01"; not valid ISO date
    start_date: str | None = None
    end_date: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    industry_context: str | None = None
    team_size: int | None = None
    budget_managed: str | None = None


class EducationEntry(BaseModel):
    institution: str
    degree: str
    field: str = ""
    start_date: str | None = None
    end_date: str | None = None
    grade: str | None = None
    thesis_title: str | None = None
    relevant_coursework: list[str] = Field(default_factory=list)


class Certification(BaseModel):
    name: str
    issuing_organization: str
    date_obtained: date | None = None
    expiry_date: date | None = None  # None means doesn't expire
    credential_id: str | None = None
    credential_url: str | None = None


class Skill(BaseModel):
    name: str
    category: Literal["technical", "soft", "language", "domain"] = "technical"
    proficiency: Literal["basic", "intermediate", "advanced", "expert"] = "intermediate"
    years_experience: int | None = None
    source: str | None = None  # which role/interview surfaced this
    last_used: date | None = None


class Language(BaseModel):
    language: str
    level: str


class Publication(BaseModel):
    title: str
    type: Literal["publication", "patent"] = "publication"
    co_authors: list[str] = Field(default_factory=list)
    venue: str | None = None  # journal, conference, or patent office
    published_date: date | None = None
    doi: str | None = None
    url: str | None = None
    patent_number: str | None = None


class VolunteerActivity(BaseModel):
    role: str
    organization: str
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None  # None means ongoing
    description: str | None = None
    cause: str | None = None  # e.g. "Education", "Environment"


# ─── Merge conflict model (stored in metadata, resolved by user) ──────────────

class Conflict(BaseModel):
    conflict_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    section: str
    field: str
    existing_value: Any
    incoming_value: Any
    source: str  # which CV/import caused this
    suggested_resolution: str | None = None
    resolved: bool = False


# ─── Enrichment tracking ──────────────────────────────────────────────────────

class FieldChange(BaseModel):
    section: str
    field: str
    action: Literal["added", "updated", "merged"]
    old_value: Any | None = None
    new_value: Any


class EnrichmentRecord(BaseModel):
    timestamp: datetime
    source: Literal["cv_upload", "linkedin_import", "xing_import", "interview", "manual_edit"]
    source_session_id: str | None = None
    changes: list[FieldChange] = Field(default_factory=list)
    confidence: float | None = None  # for LLM-extracted data


# ─── Profile metadata ─────────────────────────────────────────────────────────

class ProfileMetadata(BaseModel):
    completeness_score: float = 0.0  # 0.0 to 1.0
    created_via: Literal["cv_upload", "linkedin_import", "xing_import", "interview", "manual"] = "manual"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    application_count: int = 0
    enrichment_history: list[EnrichmentRecord] = Field(default_factory=list)
    pending_conflicts: list[Conflict] = Field(default_factory=list)


# ─── Completeness calculation ─────────────────────────────────────────────────

_COMPLETENESS_WEIGHTS: dict[str, float] = {
    "work_experience": 0.30,
    "education": 0.20,
    "skills": 0.20,
    "personal_info": 0.15,
    "languages": 0.10,
    "professional_summary": 0.03,
    "certifications": 0.01,
    "publications": 0.005,
    "volunteer_activities": 0.005,
}


def _has_meaningful_data(profile: "MasterProfileData", section: str) -> bool:
    value = getattr(profile, section, None)
    if value is None:
        return False
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, PersonalInfo):
        return bool(value.name or value.email)
    if isinstance(value, ProfessionalSummary):
        return bool(value.de or value.en)
    return bool(value)


# ─── Master profile data ──────────────────────────────────────────────────────

class MasterProfileData(BaseModel):
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    professional_summary: ProfessionalSummary = Field(default_factory=ProfessionalSummary)
    work_experience: list[WorkEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    volunteer_activities: list[VolunteerActivity] = Field(default_factory=list)
    metadata: ProfileMetadata | None = None

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_fields(cls, data: Any) -> Any:
        """Migrate old JSONB keys → new field names so existing DB records load cleanly."""
        if not isinstance(data, dict):
            return data

        # work_history → work_experience; bullets → responsibilities
        if "work_history" in data and "work_experience" not in data:
            migrated = []
            for e in data.pop("work_history"):
                entry = dict(e)
                if "bullets" in entry and "responsibilities" not in entry:
                    entry["responsibilities"] = entry.pop("bullets")
                migrated.append(entry)
            data["work_experience"] = migrated

        # contact → personal_info; linkedin → linkedin_url
        if "contact" in data and "personal_info" not in data:
            c = dict(data.pop("contact"))
            if "linkedin" in c and "linkedin_url" not in c:
                c["linkedin_url"] = c.pop("linkedin")
            data["personal_info"] = c

        # skills: list[str] → list[Skill]
        if "skills" in data and isinstance(data["skills"], list):
            skills = []
            for s in data["skills"]:
                if isinstance(s, str):
                    skills.append({"name": s, "category": "technical", "proficiency": "intermediate"})
                else:
                    skills.append(s)
            data["skills"] = skills

        return data

    def calculate_completeness(self) -> float:
        score = 0.0
        for section, weight in _COMPLETENESS_WEIGHTS.items():
            if _has_meaningful_data(self, section):
                score += weight
        return round(score, 2)


# ─── API response models ──────────────────────────────────────────────────────

class MasterProfileResponse(BaseModel):
    id: uuid.UUID
    profile: MasterProfileData
    completeness: float  # 0.0 to 1.0
    merge_conflicts: list[Conflict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LinkedInImportRequest(BaseModel):
    linkedin_json: dict
