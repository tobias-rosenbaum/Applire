import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.auth import get_auth_provider
from apliqa.auth.base import AuthProvider
from apliqa.db.session import get_db
from apliqa.exceptions import LLMRateLimitError, LLMTimeoutError
from apliqa.providers import get_provider
from apliqa.providers.llm.base import LLMProvider
from apliqa.schemas.gap import GapAnalysisResponse
from apliqa.schemas.job import JobAnalyzeRequest, JobAnalysisResponse
from apliqa.services.gap import analyze_gaps
from apliqa.services.job import analyze_jd
from apliqa.services.scraper import ScraperError, scrape_job_url

router = APIRouter(prefix="/api/job", tags=["job"])


def _get_provider() -> LLMProvider:
    return get_provider()


@router.post("/analyze", response_model=JobAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_job_description(
    body: JobAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(_get_provider),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> JobAnalysisResponse:
    if body.url:
        try:
            text = await scrape_job_url(body.url)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )
        except ScraperError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.reason,
            )
        source_url = body.url
    else:
        text = body.text.strip()  # type: ignore[union-attr]
        source_url = None

    try:
        return await analyze_jd(text, db, provider, source_url=source_url)
    except LLMTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc))
    except LLMRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned invalid JSON",
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post(
    "/{job_id}/gaps",
    response_model=GapAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def get_gap_analysis(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(_get_provider),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> GapAnalysisResponse:
    try:
        return await analyze_gaps(job_id, db, provider)
    except LLMTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc))
    except LLMRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned invalid JSON",
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
