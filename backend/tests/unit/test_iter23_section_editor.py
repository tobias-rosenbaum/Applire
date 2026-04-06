# backend/tests/unit/test_iter23_section_editor.py
"""Unit tests for Sprint 9 CV Section Editor endpoints (23.14)."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from applire.auth import get_auth_provider
from applire.db.session import get_db
from applire.routers.cv import router

_CV_ID = str(uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
_SECTION_ID = "introduction"
_POSITION_UUID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
_POSITION_SECTION_ID = f"position::{_POSITION_UUID}"


async def _stub_db():
    yield None


@pytest.fixture()
def client():
    app = FastAPI()
    app.dependency_overrides[get_auth_provider] = lambda: None
    app.dependency_overrides[get_db] = _stub_db
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# GET /api/cv/{id}/sections
# ---------------------------------------------------------------------------


def test_get_sections_returns_200_with_sections(client):
    from applire.schemas.cv_sections import CVSectionsResponse, SectionItem, GapHintItem
    mock_response = CVSectionsResponse(
        sections=[
            SectionItem(
                section_id="introduction",
                label="Introduction",
                content="Experienced developer",
                has_override=False,
                gaps=[GapHintItem(id="Python", label="Python")],
            )
        ],
        general_gaps=[],
    )
    with patch(
        "applire.routers.cv.get_cv_sections",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.get(f"/api/cv/{_CV_ID}/sections")

    assert response.status_code == 200
    data = response.json()
    assert len(data["sections"]) == 1
    assert data["sections"][0]["section_id"] == "introduction"
    assert data["sections"][0]["gaps"][0]["label"] == "Python"


def test_get_sections_returns_404_when_cv_not_found(client):
    with patch(
        "applire.routers.cv.get_cv_sections",
        new_callable=AsyncMock,
        side_effect=LookupError("CV not found"),
    ):
        response = client.get(f"/api/cv/{_CV_ID}/sections")

    assert response.status_code == 404


def test_get_sections_returns_empty_list_when_no_snapshot(client):
    from applire.schemas.cv_sections import CVSectionsResponse
    mock_response = CVSectionsResponse(sections=[], general_gaps=[])
    with patch(
        "applire.routers.cv.get_cv_sections",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.get(f"/api/cv/{_CV_ID}/sections")

    assert response.status_code == 200
    assert response.json()["sections"] == []


# ---------------------------------------------------------------------------
# PATCH /api/cv/{id}/sections/{section_id}
# ---------------------------------------------------------------------------


def test_patch_section_returns_html_and_overrides_applied(client):
    from applire.schemas.cv_sections import SectionPatchResponse
    mock_response = SectionPatchResponse(
        html="<html><body>Updated CV</body></html>",
        overrides_applied=["introduction"],
    )
    with patch(
        "applire.routers.cv.patch_cv_section",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.patch(
            f"/api/cv/{_CV_ID}/sections/{_SECTION_ID}",
            json={"content": "My edited summary", "save_to_profile": False},
        )

    assert response.status_code == 200
    data = response.json()
    assert "<html>" in data["html"]
    assert "introduction" in data["overrides_applied"]


def test_patch_section_returns_422_for_invalid_section_id(client):
    with patch(
        "applire.routers.cv.patch_cv_section",
        new_callable=AsyncMock,
        side_effect=ValueError("Unknown section_id: 'nonexistent'"),
    ):
        response = client.patch(
            f"/api/cv/{_CV_ID}/sections/nonexistent",
            json={"content": "text", "save_to_profile": False},
        )

    assert response.status_code == 422


def test_patch_section_rejects_content_over_10000_chars(client):
    """Pydantic max_length=10_000 validation fires before the service is called."""
    long_content = "x" * 10_001
    response = client.patch(
        f"/api/cv/{_CV_ID}/sections/{_SECTION_ID}",
        json={"content": long_content, "save_to_profile": False},
    )
    assert response.status_code == 422


def test_patch_section_passes_save_to_profile_true(client):
    from applire.schemas.cv_sections import SectionPatchResponse
    mock_service = AsyncMock(
        return_value=SectionPatchResponse(
            html="<html></html>",
            overrides_applied=["introduction"],
        )
    )
    with patch("applire.routers.cv.patch_cv_section", new=mock_service):
        client.patch(
            f"/api/cv/{_CV_ID}/sections/{_SECTION_ID}",
            json={"content": "text", "save_to_profile": True},
        )

    mock_service.assert_called_once()
    call_args = mock_service.call_args.args
    # patch_cv_section(cv_id, section_id, content, save_to_profile, db)
    assert call_args[3] is True  # save_to_profile is the 4th positional arg


def test_patch_section_position_id_with_double_colon(client):
    """Verify the :path converter captures position::uuid correctly."""
    from applire.schemas.cv_sections import SectionPatchResponse
    mock_service = AsyncMock(
        return_value=SectionPatchResponse(
            html="<html></html>",
            overrides_applied=[_POSITION_SECTION_ID],
        )
    )
    with patch("applire.routers.cv.patch_cv_section", new=mock_service):
        response = client.patch(
            f"/api/cv/{_CV_ID}/sections/{_POSITION_SECTION_ID}",
            json={"content": "Built APIs\nLed team", "save_to_profile": False},
        )

    assert response.status_code == 200
    call_args = mock_service.call_args.args
    assert call_args[1] == _POSITION_SECTION_ID  # section_id captured with ::


# ---------------------------------------------------------------------------
# GET /api/cv/{id}/html — regression: overrides applied but endpoint still works
# ---------------------------------------------------------------------------


def test_html_endpoint_still_returns_html_with_overrides_applied(client):
    test_html = "<html><body>Patched CV</body></html>"
    with patch("applire.routers.cv.get_cv_html", new_callable=AsyncMock, return_value=test_html):
        response = client.get(f"/api/cv/{_CV_ID}/html")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Patched CV" in response.text


# ---------------------------------------------------------------------------
# Unit tests for build_content_snapshot
# ---------------------------------------------------------------------------


def test_build_content_snapshot_extracts_all_fields():
    from applire.services.cv_section_editor import build_content_snapshot
    from applire.schemas.cv import TailoredCVData, TailoredWorkEntry, TailoredContact

    tailored = TailoredCVData(
        contact=TailoredContact(name="Max"),
        summary="Experienced Python developer",
        work_history=[
            TailoredWorkEntry(
                company="ACME",
                role="Engineer",
                start_date="2020-01",
                end_date="2023-12",
                bullets=["Built APIs", "Led team"],
            )
        ],
        skills=["Python", "FastAPI"],
    )

    snapshot = build_content_snapshot(tailored)

    assert snapshot["introduction"] == "Experienced Python developer"
    assert snapshot["skills"] == ["Python", "FastAPI"]
    assert len(snapshot["positions"]) == 1
    pos = snapshot["positions"][0]
    assert pos["title"] == "Engineer"
    assert pos["company"] == "ACME"
    assert pos["bullets"] == ["Built APIs", "Led team"]
    assert pos["index"] == 0
    uuid.UUID(pos["id"])  # raises ValueError if not valid UUID


def test_apply_overrides_replaces_introduction():
    from applire.services.cv_section_editor import apply_overrides_to_tailored
    from applire.schemas.cv import TailoredCVData, TailoredContact

    tailored = TailoredCVData(
        contact=TailoredContact(name="Max"),
        summary="Original summary",
        work_history=[],
        skills=[],
    )
    result = apply_overrides_to_tailored(
        tailored,
        content_snapshot=None,
        section_overrides={"introduction": "My new summary"},
    )
    assert result.summary == "My new summary"


def test_apply_overrides_replaces_skills():
    from applire.services.cv_section_editor import apply_overrides_to_tailored
    from applire.schemas.cv import TailoredCVData, TailoredContact

    tailored = TailoredCVData(
        contact=TailoredContact(name="Max"),
        summary="",
        work_history=[],
        skills=["Java"],
    )
    result = apply_overrides_to_tailored(
        tailored,
        content_snapshot=None,
        section_overrides={"skills": "Python\nFastAPI\nPostgreSQL"},
    )
    assert result.skills == ["Python", "FastAPI", "PostgreSQL"]


def test_apply_overrides_with_no_overrides_returns_unchanged():
    from applire.services.cv_section_editor import apply_overrides_to_tailored
    from applire.schemas.cv import TailoredCVData, TailoredContact

    tailored = TailoredCVData(
        contact=TailoredContact(name="Max"),
        summary="Original",
        work_history=[],
        skills=["Java"],
    )
    result = apply_overrides_to_tailored(tailored, None, None)
    assert result.summary == "Original"
    assert result is tailored  # same object — no copy made
