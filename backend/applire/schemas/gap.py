import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GapAnalysisResponse(BaseModel):
    id: uuid.UUID
    job_analysis_id: uuid.UUID
    profile_id: uuid.UUID
    match_score: float = Field(ge=0.0, le=1.0)
    critical_gaps: list[str]
    minor_gaps: list[str]
    strengths: list[str]
    keyword_gaps: list[str]
    category_a: list[str] = Field(default_factory=list)
    category_b: list[str] = Field(default_factory=list)
    category_c: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}
