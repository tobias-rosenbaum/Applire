"""My Documents — response schemas for GET /api/documents."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from applire.models.cv import CVGenerationStatus


class DocumentItem(BaseModel):
    cv_id: uuid.UUID
    flow_id: uuid.UUID | None
    role_title: str | None
    company_name: str | None
    template: str
    status: CVGenerationStatus
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentItem]
    total: int
