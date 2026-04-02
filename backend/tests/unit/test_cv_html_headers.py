# backend/tests/unit/test_cv_html_headers.py
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apliqa.auth import get_auth_provider
from apliqa.db.session import get_db
from apliqa.routers.cv import router

_TEST_CV_ID = str(uuid.UUID("12345678-1234-1234-1234-123456789012"))
_TEST_HTML = "<html><body><p>Max Mustermann</p></body></html>"


async def _stub_db():
    """Async generator stub — provides a None session, satisfying the Depends(get_db) contract."""
    yield None


@pytest.fixture()
def client():
    """Fresh minimal app per test, with auth and db overridden."""
    app = FastAPI()
    app.dependency_overrides[get_auth_provider] = lambda: None
    app.dependency_overrides[get_db] = _stub_db
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=True)


def test_html_endpoint_has_no_x_frame_options_header(client):
    with patch("apliqa.routers.cv.get_cv_html", new_callable=AsyncMock, return_value=_TEST_HTML):
        response = client.get(f"/api/cv/{_TEST_CV_ID}/html")

    assert response.status_code == 200
    assert "x-frame-options" not in response.headers


def test_html_endpoint_has_no_csp_frame_ancestors_header(client):
    with patch("apliqa.routers.cv.get_cv_html", new_callable=AsyncMock, return_value=_TEST_HTML):
        response = client.get(f"/api/cv/{_TEST_CV_ID}/html")

    assert response.status_code == 200
    assert "content-security-policy" not in response.headers


def test_html_endpoint_returns_html_content_type(client):
    with patch("apliqa.routers.cv.get_cv_html", new_callable=AsyncMock, return_value=_TEST_HTML):
        response = client.get(f"/api/cv/{_TEST_CV_ID}/html")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
