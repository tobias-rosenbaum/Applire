# Copyright (C) 2024-2026 Tobias Rosenbaum
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Endpoint tests for POST /api/profile/roles."""
import pytest
from httpx import AsyncClient

from applire.main import app
from applire.schemas.profile import MasterProfileData, ProfileMetadata, WorkEntry


@pytest.mark.asyncio
async def test_add_role_minimal(seed_profile, async_client: AsyncClient):
    profile = MasterProfileData(metadata=ProfileMetadata())
    await seed_profile(profile)

    res = await async_client.post(
        "/api/profile/roles",
        json={
            "title": "Director of QA",
            "company": "Roche",
            "start_date": "2026-06-01",
            "close_roles": [],
            "source": "manual",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["new_role_id"]
    assert body["closed_role_ids"] == []
    assert 0.0 <= body["completeness_score"] <= 1.0


@pytest.mark.asyncio
async def test_add_role_closes_existing(seed_profile, async_client: AsyncClient):
    existing = WorkEntry(company="A", role="Lead", start_date="2023-01-01", end_date=None)
    await seed_profile(MasterProfileData(
        work_experience=[existing],
        metadata=ProfileMetadata(),
    ))

    res = await async_client.post(
        "/api/profile/roles",
        json={
            "title": "Director",
            "company": "B",
            "start_date": "2026-06-01",
            "close_roles": [{"role_id": existing.id, "end_date": "2026-05-31"}],
            "source": "manual",
        },
    )
    assert res.status_code == 200
    assert res.json()["closed_role_ids"] == [existing.id]


@pytest.mark.asyncio
async def test_add_role_422_on_unknown_close_id(seed_profile, async_client: AsyncClient):
    await seed_profile(MasterProfileData(metadata=ProfileMetadata()))
    res = await async_client.post(
        "/api/profile/roles",
        json={
            "title": "Director", "company": "B", "start_date": "2026-06-01",
            "close_roles": [{"role_id": "does-not-exist", "end_date": "2026-05-31"}],
            "source": "manual",
        },
    )
    assert res.status_code == 422
