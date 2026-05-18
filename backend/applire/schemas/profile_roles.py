# Copyright (C) 2024-2026 Tobias Rosenbaum
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Request/response models for POST /api/profile/roles.

Adds a new work entry to the Master Profile and (optionally) sets end_date on
0..n existing open roles in a single transaction. See spec
docs/superpowers/specs/2026-05-18-post-hire-profile-refresh-design.md
"""
from typing import Literal

from pydantic import BaseModel, Field


SourceType = Literal["application", "jd_paste", "manual"]


class CloseRoleEntry(BaseModel):
    role_id: str
    end_date: str  # YYYY-MM-DD; string to match WorkEntry.end_date


class AddRoleRequest(BaseModel):
    title: str
    company: str
    start_date: str  # YYYY-MM-DD
    location: str | None = None
    industry: str | None = None
    close_roles: list[CloseRoleEntry] = Field(default_factory=list)
    source: SourceType
    source_ref: str | None = None


class AddRoleResponse(BaseModel):
    profile_id: str
    new_role_id: str
    closed_role_ids: list[str] = Field(default_factory=list)
    completeness_score: float
