"""Flow Orchestrator — Iteration 15

Manages the end-to-end user journey from JD intake to CV download.

State lives in flow_sessions (server-side, per ADR 004 Stateful Backend principle).
The step graph is a validated linear DAG — no illegal jumps.

Write path (advance_flow): caller passes artifact_id explicitly; FK written atomically
with the step transition to prevent race conditions with stale sibling flows.

Read path (get_flow_state): eager-loads child summaries via the FKs already set on
the flow record — deterministic, no discovery queries needed.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.constants import MODE_B_COMPLETENESS_THRESHOLD
from apliqa.models.cv import GeneratedCV
from apliqa.models.flow import FlowSession
from apliqa.models.gap import GapAnalysis
from apliqa.models.job import JobAnalysis
from apliqa.models.profile import MasterProfile
from apliqa.models.session import InterviewSession
from apliqa.schemas.flow import (
    AdvanceFlowRequest,
    CreateFlowRequest,
    CreateFlowResponse,
    CVSummary,
    FlowStateResponse,
    GapAnalysisSummary,
    InterviewSummary,
    JobAnalysisSummary,
)
from apliqa.schemas.profile import MasterProfileData

# ---------------------------------------------------------------------------
# Step graph
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[str, list[str]] = {
    "jd_analysis":   ["cv_import", "gap_analysis"],   # returning users skip cv_import
    "cv_import":     ["gap_analysis"],
    "gap_analysis":  ["interview", "cv_generation"],   # returning users may skip interview
    "interview":     ["cv_generation"],
    "cv_generation": ["complete"],
    "complete":      [],
}

# Steps that require an artifact_id when advanced into — field name on FlowSession
_ARTIFACT_FIELD: dict[str, str] = {
    "gap_analysis":   "gap_analysis_id",
    "interview":      "interview_session_id",
    "cv_generation":  "generated_cv_id",
}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class InvalidTransitionError(Exception):
    def __init__(self, current: str, target: str, allowed: list[str]) -> None:
        self.current = current
        self.target = target
        self.allowed = allowed
        super().__init__(
            f"Cannot transition from '{current}' to '{target}'. Allowed: {allowed}"
        )


class ArtifactRequiredError(Exception):
    def __init__(self, step: str, field: str) -> None:
        self.step = step
        self.field = field
        super().__init__(
            f"Advancing to '{step}' requires artifact_id ({field}) but none was provided."
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def create_flow(
    request: CreateFlowRequest,
    user_id: uuid.UUID,
    db: AsyncSession,
    base_url: str = "http://localhost:8001",
) -> CreateFlowResponse:
    """Create or resume a flow session for (user_id, job_id).

    Idempotent: if a flow already exists for this (user_id, job_id), returns it.
    """
    job = await db.get(JobAnalysis, request.job_id)
    if job is None:
        raise LookupError(f"Job {request.job_id} not found")

    existing = await _get_existing_flow(user_id, request.job_id, db)
    if existing is not None:
        return CreateFlowResponse(
            flow_id=existing.id,
            user_type=existing.user_type,
            current_step=existing.current_step,
            available_actions=existing.available_actions,
            job_summary=JobAnalysisSummary(job_id=job.id, role_title=job.role_title),
        )

    user_type = await _resolve_user_type(db)
    available_actions = _compute_actions("jd_analysis", user_type)

    flow = FlowSession(
        user_id=user_id,
        job_id=request.job_id,
        current_step="jd_analysis",
        user_type=user_type,
        available_actions=available_actions,
    )
    db.add(flow)
    try:
        await db.commit()
    except IntegrityError:
        # Race: another request created the flow between our check and insert
        await db.rollback()
        existing = await _get_existing_flow(user_id, request.job_id, db)
        if existing is None:
            raise
        flow = existing

    await db.refresh(flow)
    return CreateFlowResponse(
        flow_id=flow.id,
        user_type=flow.user_type,
        current_step=flow.current_step,
        available_actions=flow.available_actions,
        job_summary=JobAnalysisSummary(job_id=job.id, role_title=job.role_title),
    )


async def get_flow_state(
    flow_id: uuid.UUID,
    db: AsyncSession,
    base_url: str = "http://localhost:8001",
) -> FlowStateResponse:
    """Return the full flow state with eagerly-loaded child resource summaries."""
    flow = await db.get(FlowSession, flow_id)
    if flow is None:
        raise LookupError(f"Flow {flow_id} not found")
    return await _build_state_response(flow, db, base_url)


async def advance_flow(
    flow_id: uuid.UUID,
    request: AdvanceFlowRequest,
    db: AsyncSession,
    base_url: str = "http://localhost:8001",
) -> FlowStateResponse:
    """Validate and apply a step transition, writing artifact FK atomically."""
    flow = await db.get(FlowSession, flow_id)
    if flow is None:
        raise LookupError(f"Flow {flow_id} not found")

    target = request.step
    allowed = VALID_TRANSITIONS.get(flow.current_step, [])
    if target not in allowed:
        raise InvalidTransitionError(
            current=flow.current_step, target=target, allowed=allowed
        )

    if target in _ARTIFACT_FIELD:
        field = _ARTIFACT_FIELD[target]
        if request.artifact_id is None:
            raise ArtifactRequiredError(step=target, field=field)
        setattr(flow, field, request.artifact_id)

    flow.current_step = target
    flow.available_actions = _compute_actions(target, flow.user_type)
    flow.updated_at = datetime.now(timezone.utc)
    if target == "complete":
        flow.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(flow)
    return await _build_state_response(flow, db, base_url)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


async def _get_existing_flow(
    user_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession
) -> FlowSession | None:
    result = await db.execute(
        select(FlowSession).where(
            FlowSession.user_id == user_id,
            FlowSession.job_id == job_id,
        )
    )
    return result.scalar_one_or_none()


async def _resolve_user_type(db: AsyncSession) -> str:
    """Return 'returning' if profile completeness >= MODE_B_COMPLETENESS_THRESHOLD."""
    result = await db.execute(select(MasterProfile).limit(1))
    profile_record = result.scalar_one_or_none()
    if profile_record is None:
        return "new"
    try:
        profile_data = MasterProfileData.model_validate(profile_record.profile_json)
        score = profile_data.calculate_completeness()
    except Exception:
        return "new"
    return "returning" if score >= MODE_B_COMPLETENESS_THRESHOLD else "new"


def _compute_actions(step: str, user_type: str) -> dict[str, str]:
    """Return available_actions dict for a given (step, user_type)."""
    if step == "jd_analysis":
        return {"next": "gap_analysis"} if user_type == "returning" else {"next": "cv_import"}
    if step == "cv_import":
        return {"next": "gap_analysis"}
    if step == "gap_analysis":
        if user_type == "returning":
            return {"next": "cv_generation"}
        return {"next": "interview", "skip": "cv_generation"}
    if step == "interview":
        return {"next": "cv_generation"}
    if step == "cv_generation":
        return {"next": "complete"}
    return {}


async def _build_state_response(
    flow: FlowSession,
    db: AsyncSession,
    base_url: str,
) -> FlowStateResponse:
    # Job summary
    job_summary: JobAnalysisSummary | None = None
    job = await db.get(JobAnalysis, flow.job_id)
    if job:
        job_summary = JobAnalysisSummary(job_id=job.id, role_title=job.role_title)

    # Profile completeness
    profile_completeness: float | None = None
    result = await db.execute(select(MasterProfile).limit(1))
    profile_record = result.scalar_one_or_none()
    if profile_record:
        try:
            profile_data = MasterProfileData.model_validate(profile_record.profile_json)
            profile_completeness = profile_data.calculate_completeness()
        except Exception:
            pass

    # Gap summary — via FK set by advance_flow
    gap_summary: GapAnalysisSummary | None = None
    if flow.gap_analysis_id:
        gap = await db.get(GapAnalysis, flow.gap_analysis_id)
        if gap:
            gap_summary = GapAnalysisSummary(
                gap_analysis_id=gap.id,
                match_score=gap.match_score,
                critical_gaps_count=len(gap.critical_gaps),
                category_c_count=len(gap.category_c),
            )

    # Interview summary — via FK set by advance_flow
    interview_summary: InterviewSummary | None = None
    if flow.interview_session_id:
        session = await db.get(InterviewSession, flow.interview_session_id)
        if session:
            interview_summary = InterviewSummary(
                session_id=session.id,
                mode=session.mode,
                status=session.status,
                questions_asked=session.questions_asked,
                hard_ceiling=session.hard_ceiling,
            )

    # CV summary — via FK set by advance_flow
    cv_summary: CVSummary | None = None
    if flow.generated_cv_id:
        cv = await db.get(GeneratedCV, flow.generated_cv_id)
        if cv:
            cv_summary = CVSummary(
                cv_id=cv.id,
                pdf_url=f"{base_url}/api/cv/{cv.id}/pdf",
                expires_at=cv.expires_at,
            )

    return FlowStateResponse(
        flow_id=flow.id,
        job_id=flow.job_id,
        user_type=flow.user_type,
        current_step=flow.current_step,
        available_actions=flow.available_actions,
        job_summary=job_summary,
        profile_completeness=profile_completeness,
        gap_summary=gap_summary,
        interview_summary=interview_summary,
        cv_summary=cv_summary,
        created_at=flow.created_at,
        updated_at=flow.updated_at,
    )
