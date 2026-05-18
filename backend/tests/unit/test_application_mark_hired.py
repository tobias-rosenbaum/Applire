# Copyright (C) 2024-2026 Tobias Rosenbaum
# SPDX-License-Identifier: AGPL-3.0-or-later
"""POST /api/applications/{id}/mark-hired."""
import uuid

import pytest
from httpx import AsyncClient

from applire.models.application import Application, UserStatus


@pytest.mark.asyncio
async def test_mark_hired_happy_path(seed_application, async_client: AsyncClient):
    app_row: Application = await seed_application(user_status=UserStatus.applied.value)
    res = await async_client.post(f"/api/applications/{app_row.id}/mark-hired")
    assert res.status_code == 200
    body = res.json()
    assert body["user_status"] == "hired"
    assert body["application_id"] == str(app_row.id)
    expected_url = f"/profile/upload?action=add-role&source=application&application_id={app_row.id}"
    assert body["redirect_url"] == expected_url


@pytest.mark.asyncio
async def test_mark_hired_is_idempotent(seed_application, async_client: AsyncClient):
    app_row: Application = await seed_application(user_status=UserStatus.hired.value)
    res = await async_client.post(f"/api/applications/{app_row.id}/mark-hired")
    assert res.status_code == 200
    assert res.json()["user_status"] == "hired"


@pytest.mark.asyncio
async def test_mark_hired_404_on_unknown(async_client: AsyncClient):
    res = await async_client.post(f"/api/applications/{uuid.uuid4()}/mark-hired")
    assert res.status_code == 404
