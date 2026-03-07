import uuid

from pydantic import BaseModel, field_validator


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
