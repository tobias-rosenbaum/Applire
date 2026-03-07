import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GapAnalysisResponse(BaseModel):
    id: uuid.UUID
    job_analysis_id: uuid.UUID
    profile_id: uuid.UUID
    match_score: int = Field(ge=0, le=100)
    critical_gaps: list[str]
    minor_gaps: list[str]
    strengths: list[str]
    keyword_gaps: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
