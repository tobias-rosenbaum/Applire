"""My Documents service — list generated CVs across all jobs for a user."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from applire.models.application import Application
from applire.models.cv import GeneratedCV
from applire.schemas.documents import DocumentItem, DocumentListResponse


async def list_documents(
    *,
    user_id: uuid.UUID,
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
) -> DocumentListResponse:
    """Return all non-deleted CVs for *user_id*, newest first.

    Joins generated_cvs → applications to get role_title, company_name and
    flow_session_id without touching master_profiles.
    """
    base = (
        select(GeneratedCV, Application)
        .join(Application, GeneratedCV.job_analysis_id == Application.job_analysis_id)
        .where(
            Application.user_id == user_id,
            GeneratedCV.deleted_at.is_(None),
            Application.deleted_at.is_(None),
        )
    )
    if status:
        base = base.where(GeneratedCV.status == status)

    # Total count
    count_q = select(func.count()).select_from(base.subquery())
    total: int = (await db.execute(count_q)).scalar_one()

    # Paginated rows, newest first
    rows_q = (
        base.order_by(GeneratedCV.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(rows_q)).all()

    items = [
        DocumentItem(
            cv_id=cv.id,
            flow_id=app.flow_session_id,
            role_title=app.role_title,
            company_name=app.company_name,
            template=cv.template,
            status=cv.status,
            created_at=cv.created_at,
            expires_at=cv.expires_at,
        )
        for cv, app in rows
    ]
    return DocumentListResponse(items=items, total=total)
