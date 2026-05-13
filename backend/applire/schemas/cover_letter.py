# Copyright (C) 2024-2026 Tobias Rosenbaum
#
# This file is part of Applire.
#
# Applire is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Applire is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Applire. If not, see <https://www.gnu.org/licenses/>.

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from applire.models.cover_letter import CoverLetterStatus

CLTemplate = Literal[
    "classic_german",
    "modern_swiss",
    "executive",
    "tech_developer",
    "creative_sidebar",
    "academic",
    "compact_pro",
]

CLTone = Literal["formal", "professional", "conversational"]


class CoverLetterGenerateRequest(BaseModel):
    job_id: uuid.UUID
    recipient_name: Optional[str] = None
    recipient_company: Optional[str] = None
    salary: Optional[str] = None
    availability: Optional[str] = None
    motivation: Optional[str] = None
    tone: CLTone = "formal"


class CoverLetterGenerateResponse(BaseModel):
    cover_letter_id: uuid.UUID
    status: CoverLetterStatus
    html_url: str
    pdf_url: str
    expires_at: datetime


class CoverLetterStatusResponse(BaseModel):
    cover_letter_id: uuid.UUID
    status: CoverLetterStatus
    html_url: Optional[str] = None
    pdf_url: Optional[str] = None
    error_message: Optional[str] = None
    expires_at: datetime
    letter_data: Optional[dict] = None  # populated only when status == ready

    model_config = {"from_attributes": True}


class SectionOverridePatch(BaseModel):
    section: Literal["header", "recipient", "body", "signature"]
    content: str


class SectionOverridePatchResponse(BaseModel):
    cover_letter_id: uuid.UUID
    section: str
    status: str = "saved"


class CoverLetterSummaryResponse(BaseModel):
    cover_letter_id: uuid.UUID
    status: CoverLetterStatus
    template: str
    html_url: Optional[str] = None
    pdf_url: Optional[str] = None
    expires_at: datetime

    model_config = {"from_attributes": True}
