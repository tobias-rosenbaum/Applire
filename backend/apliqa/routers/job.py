import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.db.session import get_db
from apliqa.providers import get_provider
from apliqa.providers.base import LLMProvider
from apliqa.schemas.gap import GapAnalysisResponse
from apliqa.schemas.job import JobAnalyzeRequest, JobAnalysisResponse
from apliqa.services.gap import analyze_gaps
from apliqa.services.job import analyze_jd

router = APIRouter(prefix="/api/job", tags=["job"])

_LLM_TIMEOUT_SECONDS = 30.0


def _get_provider() -> LLMProvider:
    return get_provider()


@router.post("/analyze", response_model=JobAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_job_description(
    body: JobAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(_get_provider),
) -> JobAnalysisResponse:
    if not body.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="text must not be empty",
        )

    try:
        return await asyncio.wait_for(
            analyze_jd(body.text.strip(), db, provider),
            timeout=_LLM_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LLM request timed out",
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned invalid JSON",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post(
    "/{job_id}/gaps",
    response_model=GapAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def get_gap_analysis(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(_get_provider),
) -> GapAnalysisResponse:
    try:
        return await asyncio.wait_for(
            analyze_gaps(job_id, db, provider),
            timeout=_LLM_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LLM request timed out",
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned invalid JSON",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
