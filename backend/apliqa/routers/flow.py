import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.auth import get_auth_provider
from apliqa.auth.base import AuthProvider
from apliqa.db.session import get_db
from apliqa.schemas.flow import (
    AdvanceFlowRequest,
    CreateFlowRequest,
    CreateFlowResponse,
    FlowStateResponse,
)
from apliqa.services.flow.orchestrator import (
    ArtifactRequiredError,
    InvalidTransitionError,
    advance_flow,
    create_flow,
    get_flow_state,
)

router = APIRouter(prefix="/api/flow", tags=["flow"])


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


@router.post("", response_model=CreateFlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow_session(
    body: CreateFlowRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: AuthProvider = Depends(get_auth_provider),
) -> CreateFlowResponse:
    """Create or resume a flow session for a job.

    Resolves user_type (new/returning) from profile completeness.
    Idempotent: returns the existing flow if one exists for (user_id, job_id).
    """
    user = await auth.get_current_user(request)
    try:
        return await create_flow(body, user.id, db, base_url=_base_url(request))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{flow_id}/state", response_model=FlowStateResponse)
async def get_flow_state_endpoint(
    flow_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> FlowStateResponse:
    """Return current flow step, available actions, and child resource summaries."""
    try:
        return await get_flow_state(flow_id, db, base_url=_base_url(request))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{flow_id}/advance", response_model=FlowStateResponse)
async def advance_flow_endpoint(
    flow_id: uuid.UUID,
    body: AdvanceFlowRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> FlowStateResponse:
    """Request a step transition.

    The backend validates against VALID_TRANSITIONS — illegal jumps return 409.
    For steps that produce an artifact (gap_analysis, interview, cv_generation),
    artifact_id must be provided — missing it returns 422.
    """
    try:
        return await advance_flow(flow_id, body, db, base_url=_base_url(request))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "current_step": exc.current,
                "target_step": exc.target,
                "allowed_transitions": exc.allowed,
            },
        )
    except ArtifactRequiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"artifact_id is required when advancing to '{exc.step}' "
                f"(stores it as {exc.field} on the flow record)"
            ),
        )
