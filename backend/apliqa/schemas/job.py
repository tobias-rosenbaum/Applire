import uuid

from pydantic import BaseModel, field_validator


def _coerce_to_list(v: object) -> list[str]:
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    return []


class JobAnalyzeRequest(BaseModel):
    text: str


class JobAnalysisResponse(BaseModel):
    id: uuid.UUID
    role_title: str
    required_skills: list[str]
    nice_to_have_skills: list[str]
    keywords: list[str]
    seniority_level: str
    company_culture_signals: list[str]
    language_requirement: str
    raw_text_hash: str

    model_config = {"from_attributes": True}

    @field_validator("required_skills", "nice_to_have_skills", "keywords", "company_culture_signals", mode="before")
    @classmethod
    def coerce_list_fields(cls, v: object) -> list[str]:
        return _coerce_to_list(v)
