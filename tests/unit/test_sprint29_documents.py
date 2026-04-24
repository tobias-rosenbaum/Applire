"""Sprint 29 — My Documents backend (unit tests)

Run:
    pytest tests/unit/test_sprint29_documents.py -v
"""
import uuid
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Task 1 — Schema
# ---------------------------------------------------------------------------

def test_document_item_schema():
    """DocumentItem validates correctly and accepts None flow_id."""
    from applire.schemas.documents import DocumentItem
    from applire.models.cv import CVGenerationStatus

    now = datetime.now(timezone.utc)
    item = DocumentItem(
        cv_id=uuid.uuid4(),
        flow_id=None,
        role_title="Senior Engineer",
        company_name="Roche",
        template="classic_german",
        status=CVGenerationStatus.ready,
        created_at=now,
        expires_at=now,
    )
    assert item.role_title == "Senior Engineer"
    assert item.flow_id is None


def test_document_list_response_schema():
    """DocumentListResponse wraps items and total."""
    from applire.schemas.documents import DocumentItem, DocumentListResponse
    from applire.models.cv import CVGenerationStatus

    now = datetime.now(timezone.utc)
    item = DocumentItem(
        cv_id=uuid.uuid4(),
        flow_id=uuid.uuid4(),
        role_title="QA Lead",
        company_name="Bayer",
        template="modern_swiss",
        status=CVGenerationStatus.ready,
        created_at=now,
        expires_at=now,
    )
    resp = DocumentListResponse(items=[item], total=1)
    assert resp.total == 1
    assert len(resp.items) == 1
