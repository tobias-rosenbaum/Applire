import json
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.auth import get_auth_provider
from apliqa.auth.base import AuthProvider
from apliqa.db.session import get_db
from apliqa.exceptions import LLMRateLimitError, LLMTimeoutError
from apliqa.providers import get_provider
from apliqa.providers.llm.base import LLMProvider
from apliqa.schemas.cv import CVGenerateRequest, CVGenerateResponse, CVStatusResponse
from apliqa.services.cv import generate_cv, get_cv_html, get_cv_pdf, get_cv_status

router = APIRouter(prefix="/api/cv", tags=["cv"])


def _get_provider() -> LLMProvider:
    return get_provider()


@router.post(
    "/generate",
    response_model=CVGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_generate(
    body: CVGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(_get_provider),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> CVGenerateResponse:
    """Enqueue async CV generation. Returns immediately with status='pending'.
    Poll GET /api/cv/{cv_id}/status until status='ready'."""
    try:
        return await generate_cv(body.job_id, db, provider, background_tasks, body.template)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{cv_id}/status", response_model=CVStatusResponse)
async def get_status(
    cv_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> CVStatusResponse:
    """Poll CV generation progress (17.12). Returns pdf_url/html_url only when ready."""
    base_url = str(request.base_url).rstrip("/")
    try:
        return await get_cv_status(cv_id, db, base_url)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{cv_id}/html", response_class=HTMLResponse)
async def get_html(
    cv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> HTMLResponse:
    try:
        html = await get_cv_html(cv_id, db)
        return HTMLResponse(content=html)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{cv_id}/pdf")
async def get_pdf(
    cv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> Response:
    try:
        pdf_bytes = await get_cv_pdf(cv_id, db)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="lebenslauf-{cv_id}.pdf"'},
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
