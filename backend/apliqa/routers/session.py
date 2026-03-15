import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.auth import get_auth_provider
from apliqa.auth.base import AuthProvider
from apliqa.db.session import get_db
from apliqa.providers import get_provider
from apliqa.providers.base import LLMProvider
from apliqa.schemas.gap import GapAnalysisResponse
from apliqa.schemas.session import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionMessageRequest,
    SessionMessageResponse,
)
from apliqa.services.gap import analyze_gaps_for_session
from apliqa.services.session import create_session, send_message

router = APIRouter(prefix="/api/session", tags=["session"])

_LLM_TIMEOUT_SECONDS = 30.0


def _get_provider() -> LLMProvider:
    return get_provider()


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    body: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(_get_provider),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> SessionCreateResponse:
    try:
        return await asyncio.wait_for(
            create_session(body.job_id, db, provider),
            timeout=_LLM_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LLM request timed out",
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
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
    "/{session_id}/analyze-gaps",
    response_model=GapAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_session_gaps(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(_get_provider),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> GapAnalysisResponse:
    try:
        return await asyncio.wait_for(
            analyze_gaps_for_session(session_id, db, provider),
            timeout=_LLM_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LLM request timed out",
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
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
    "/{session_id}/message",
    response_model=SessionMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def post_message(
    session_id: uuid.UUID,
    body: SessionMessageRequest,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(_get_provider),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> SessionMessageResponse:
    if not body.message.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="message must not be empty",
        )
    try:
        return await asyncio.wait_for(
            send_message(session_id, body.message.strip(), db, provider),
            timeout=_LLM_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LLM request timed out",
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
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
