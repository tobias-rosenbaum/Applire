import uuid
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator, model_validator


def _coerce_to_list(v: object) -> list[str]:
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    return []


class JobAnalyzeRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None

    @model_validator(mode="after")
    def check_exactly_one(self) -> "JobAnalyzeRequest":
        has_text = bool(self.text and self.text.strip())
        has_url = bool(self.url and self.url.strip())
        if has_text == has_url:
            raise ValueError("Provide exactly one of 'text' or 'url'.")
        if has_url:
            parsed = urlparse(self.url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError("'url' must be a valid http or https URL.")
        return self


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
    source_url: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("required_skills", "nice_to_have_skills", "keywords", "company_culture_signals", mode="before")
    @classmethod
    def coerce_list_fields(cls, v: object) -> list[str]:
        return _coerce_to_list(v)
