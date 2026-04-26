"""My Documents router — GET /api/documents."""
import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from applire.auth import get_auth_provider
from applire.auth.base import AuthProvider
from applire.db.session import get_db
from applire.schemas.documents import DocumentListResponse
from applire.services.documents import list_documents

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def get_documents(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    auth: AuthProvider = Depends(get_auth_provider),
) -> DocumentListResponse:
    """List all generated CVs for the current user, newest first."""
    user = await auth.get_current_user(request)
    return await list_documents(
        user_id=user.id,
        db=db,
        page=page,
        page_size=page_size,
        status=status,
    )
