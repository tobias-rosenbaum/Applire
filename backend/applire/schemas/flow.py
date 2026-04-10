import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Child resource summaries — lightweight DTOs for the FlowStateResponse
# ---------------------------------------------------------------------------

FlowStep = Literal[
    "jd_analysis",
    "cv_import",
    "gap_analysis",
    "interview",
    "cv_generation",
    "complete",
]


class JobAnalysisSummary(BaseModel):
    job_id: uuid.UUID
    role_title: str


class GapAnalysisSummary(BaseModel):
    gap_analysis_id: uuid.UUID
    match_score: float
    critical_gaps_count: int
    category_c_count: int


class InterviewSummary(BaseModel):
    session_id: uuid.UUID
    mode: Literal["targeted", "guided"]
    status: Literal["active", "complete"]
    questions_asked: int
    hard_ceiling: int


class CVSummary(BaseModel):
    cv_id: uuid.UUID
    pdf_url: str
    expires_at: datetime


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class CreateFlowRequest(BaseModel):
    job_id: uuid.UUID | None = None


class CreateFlowResponse(BaseModel):
    flow_id: uuid.UUID
    user_type: Literal["new", "returning"]
    current_step: FlowStep
    available_actions: dict[str, str]
    job_summary: JobAnalysisSummary | None = None


class AdvanceFlowRequest(BaseModel):
    step: str
    # Required when advancing into a step that produces an artifact:
    #   gap_analysis    → gap_analysis_id
    #   interview       → interview_session_id
    #   complete        → generated_cv_id
    artifact_id: uuid.UUID | None = None


class FlowStateResponse(BaseModel):
    flow_id: uuid.UUID
    job_id: uuid.UUID | None = None
    user_type: Literal["new", "returning"]
    current_step: FlowStep
    available_actions: dict[str, str]
    # Populated as the flow progresses
    job_summary: JobAnalysisSummary | None = None
    profile_completeness: float | None = None
    gap_summary: GapAnalysisSummary | None = None
    interview_summary: InterviewSummary | None = None
    cv_summary: CVSummary | None = None
    created_at: datetime
    updated_at: datetime
