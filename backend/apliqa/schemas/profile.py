import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WorkEntry(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: str | None = None
    bullets: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    institution: str
    degree: str
    field: str = ""
    start_date: str = ""
    end_date: str | None = None


class Language(BaseModel):
    language: str
    level: str


class Contact(BaseModel):
    name: str = ""
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None


class MasterProfileData(BaseModel):
    work_history: list[WorkEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    contact: Contact = Field(default_factory=Contact)

    def calculate_completeness(self) -> int:
        score = 0
        if self.work_history:
            score += 1
        if self.skills:
            score += 1
        if self.education:
            score += 1
        if self.languages:
            score += 1
        if self.contact.name or self.contact.email:
            score += 1
        return round(score / 5 * 100)


class MasterProfileResponse(BaseModel):
    id: uuid.UUID
    profile: MasterProfileData
    completeness: int
    created_at: datetime
    updated_at: datetime


class LinkedInImportRequest(BaseModel):
    linkedin_json: dict
