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

"""POST /api/profile/roles — add a new work entry to the Master Profile and
optionally close existing open roles. See spec
docs/superpowers/specs/2026-05-18-post-hire-profile-refresh-design.md
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from applire.auth import get_auth_provider
from applire.auth.base import AuthProvider
from applire.db.session import get_db
from applire.models.profile import MasterProfile
from applire.schemas.profile import MasterProfileData
from applire.schemas.profile_roles import AddRoleRequest, AddRoleResponse
from applire.services.profile.role_add import (
    AddRoleValidationError,
    apply_add_role,
)

router = APIRouter(prefix="/api/profile/roles", tags=["profile"])


@router.post("", response_model=AddRoleResponse)
async def add_role(
    body: AddRoleRequest,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> AddRoleResponse:
    # Load latest profile.
    result = await db.execute(
        select(MasterProfile)
        .where(MasterProfile.deleted_at.is_(None))
        .order_by(MasterProfile.created_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="No master profile found")

    profile_data = MasterProfileData.model_validate(record.profile_json)

    try:
        outcome = apply_add_role(profile_data, body)
    except AddRoleValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # Persist updated JSONB
    record.profile_json = outcome.profile.model_dump(mode="json")
    await db.commit()

    return AddRoleResponse(
        profile_id=str(record.id),
        new_role_id=outcome.new_role_id,
        closed_role_ids=outcome.closed_role_ids,
        completeness_score=outcome.profile.calculate_completeness(),
    )
