"""Application schemas — Iteration 17"""

import uuid
from datetime import datetime

from pydantic import BaseModel, model_validator

from apliqa.models.application import UserStatus, WorkflowStatus


class CreateApplicationRequest(BaseModel):
    job_analysis_id: uuid.UUID
    start_workflow: bool = False
    # User overrides for denormalized fields; falls back to LLM-extracted values
    company_name: str | None = None
    role_title: str | None = None
    notes: str | None = None
    deadline: datetime | None = None


class PatchApplicationRequest(BaseModel):
    """Only user-managed fields. workflow_status is rejected at the service layer."""
    user_status: UserStatus | None = None
    company_name: str | None = None
    role_title: str | None = None
    notes: str | None = None
    applied_at: datetime | None = None
    deadline: datetime | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "PatchApplicationRequest":
        if all(v is None for v in self.model_dump().values()):
            raise ValueError("At least one field must be provided.")
        return self


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_analysis_id: uuid.UUID
    workflow_status: WorkflowStatus
    user_status: UserStatus
    company_name: str | None
    role_title: str | None
    notes: str | None
    applied_at: datetime | None
    deadline: datetime | None
    flow_session_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]
    total: int
