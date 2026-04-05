"""Application service — Iteration 17

Manages the Application entity lifecycle:
  create     — add job to pipeline, optional immediate workflow start
  list       — user's full pipeline, filterable by status
  get        — single application detail
  patch      — update user-managed fields (rejects workflow_status writes)
  delete     — soft-delete application + attached FlowSession
  start      — create FlowSession for a tracking application (deferred activation)
  sync_status — called by Flow Orchestrator after each advance_flow() to keep
                workflow_status consistent (write-time sync, not read-time)
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.models.application import (
    Application,
    STEP_TO_WORKFLOW_STATUS,
    UserStatus,
    WorkflowStatus,
    _APPLICATION_TTL_DAYS,
)
from apliqa.models.flow import FlowSession
from apliqa.models.job import JobAnalysis
from apliqa.models.profile import MasterProfile
from apliqa.schemas.application import (
    ApplicationListResponse,
    ApplicationResponse,
    CreateApplicationRequest,
    PatchApplicationRequest,
)
from apliqa.schemas.profile import MasterProfileData

# Import flow helpers — these are pure functions with no import of application.py.
# The orchestrator imports sync_workflow_status lazily (inside advance_flow body)
# to avoid a circular import at module level.
from apliqa.services.flow.orchestrator import _compute_actions, _resolve_user_type


class ConflictError(Exception):
    """Raised when an operation violates a uniqueness or state constraint."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def create_application(
    user_id: uuid.UUID,
    request: CreateApplicationRequest,
    db: AsyncSession,
) -> ApplicationResponse:
    """Add a job to the user's pipeline.

    Denormalizes company_name / role_title from JobAnalysis if not supplied.
    If start_workflow=True, creates a FlowSession atomically in the same
    transaction (same code path as POST /api/applications/{id}/start).
    Returns HTTP 409 semantics via ConflictError if (user_id, job_id) already exists.
    """
    job = await db.get(JobAnalysis, request.job_analysis_id)
    if job is None:
        raise LookupError(f"JobAnalysis {request.job_analysis_id} not found")

    app = Application(
        user_id=user_id,
        job_analysis_id=request.job_analysis_id,
        company_name=request.company_name or job.company_name,
        role_title=request.role_title or job.role_title,
        notes=request.notes,
        deadline=request.deadline,
    )
    db.add(app)

    try:
        await db.flush()  # get app.id before potential workflow creation
    except IntegrityError:
        await db.rollback()
        raise ConflictError(
            f"Application for job {request.job_analysis_id} already exists for this user"
        )

    if request.start_workflow:
        await _start_workflow(app, user_id, db)

    await db.commit()
    await db.refresh(app)
    return ApplicationResponse.model_validate(app)


async def list_applications(
    user_id: uuid.UUID,
    db: AsyncSession,
    workflow_status: WorkflowStatus | None = None,
    user_status: UserStatus | None = None,
    q: str | None = None,
) -> ApplicationListResponse:
    stmt = (
        select(Application)
        .where(
            Application.user_id == user_id,
            Application.deleted_at.is_(None),
        )
        .order_by(Application.updated_at.desc())
    )
    if workflow_status is not None:
        stmt = stmt.where(Application.workflow_status == workflow_status.value)
    if user_status is not None:
        stmt = stmt.where(Application.user_status == user_status.value)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (Application.role_title.ilike(like))
            | (Application.company_name.ilike(like))
            | (Application.notes.ilike(like))
        )

    result = await db.execute(stmt)
    apps = result.scalars().all()

    # Batch-load FlowSessions to avoid N+1 — Application has no ORM relationship,
    # only the FK column flow_session_id.
    flow_ids = [app.flow_session_id for app in apps if app.flow_session_id is not None]
    if flow_ids:
        flow_result = await db.execute(
            select(FlowSession).where(FlowSession.id.in_(flow_ids))
        )
        flow_map: dict[uuid.UUID, FlowSession] = {
            f.id: f for f in flow_result.scalars().all()
        }
    else:
        flow_map = {}

    items = []
    for app in apps:
        data = ApplicationResponse.model_validate(app)
        if app.flow_session_id is not None:
            flow = flow_map.get(app.flow_session_id)
            if flow is not None:
                data.flow_current_step = flow.current_step
        items.append(data)
    return ApplicationListResponse(items=items, total=len(items))


async def get_application(application_id: uuid.UUID, db: AsyncSession) -> ApplicationResponse:
    app = await _get_or_404(application_id, db)
    return ApplicationResponse.model_validate(app)


async def patch_application(
    application_id: uuid.UUID,
    request: PatchApplicationRequest,
    db: AsyncSession,
) -> ApplicationResponse:
    app = await _get_or_404(application_id, db)

    if request.user_status is not None:
        app.user_status = request.user_status.value
    if request.company_name is not None:
        app.company_name = request.company_name
    if request.role_title is not None:
        app.role_title = request.role_title
    if request.notes is not None:
        app.notes = request.notes
    if request.applied_at is not None:
        app.applied_at = request.applied_at
    if request.deadline is not None:
        app.deadline = request.deadline

    _touch(app)
    await db.commit()
    await db.refresh(app)
    return ApplicationResponse.model_validate(app)


async def delete_application(application_id: uuid.UUID, db: AsyncSession) -> None:
    """Soft-delete the application and its attached FlowSession (if any)."""
    app = await _get_or_404(application_id, db)
    now = datetime.now(timezone.utc)
    app.deleted_at = now

    if app.flow_session_id is not None:
        flow = await db.get(FlowSession, app.flow_session_id)
        if flow is not None:
            flow.deleted_at = now

    await db.commit()


async def start_application_workflow(
    application_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> ApplicationResponse:
    """Create a FlowSession for a tracking application (deferred activation path).

    Returns HTTP 409 semantics via ConflictError if workflow already started.
    """
    app = await _get_or_404(application_id, db)

    if app.flow_session_id is not None:
        raise ConflictError(
            f"Workflow already started for application {application_id}"
        )

    await _start_workflow(app, user_id, db)
    _touch(app)
    await db.commit()
    await db.refresh(app)
    return ApplicationResponse.model_validate(app)


async def sync_workflow_status(
    application_id: uuid.UUID,
    new_step: str,
    db: AsyncSession,
) -> None:
    """Called by advance_flow() after a successful step transition.

    Maps the FlowSession step to a WorkflowStatus and updates the Application.
    The caller (orchestrator) is responsible for the db.commit().
    """
    new_ws = STEP_TO_WORKFLOW_STATUS.get(new_step, WorkflowStatus.analyzing)
    now = datetime.now(timezone.utc)
    await db.execute(
        update(Application)
        .where(Application.id == application_id, Application.deleted_at.is_(None))
        .values(
            workflow_status=new_ws.value,
            updated_at=now,
            expires_at=now + timedelta(days=_APPLICATION_TTL_DAYS),
        )
    )


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


async def _get_or_404(application_id: uuid.UUID, db: AsyncSession) -> Application:
    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.deleted_at.is_(None),
        )
    )
    app = result.scalar_one_or_none()
    if app is None:
        raise LookupError(f"Application {application_id} not found")
    return app


async def _start_workflow(
    app: Application,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Shared logic for create(start_workflow=True) and start_application_workflow().

    Creates a FlowSession (or reactivates a soft-deleted one), links it to the
    Application, and sets workflow_status to 'analyzing'.
    The caller is responsible for db.commit().

    uq_flow_session_user_job enforces one session per (user_id, job_id).  If a
    session already exists (e.g. from a previously deleted application for the
    same job), we reuse it rather than attempting a duplicate INSERT.
    """
    # Check for any existing session for this (user_id, job_id) — including
    # soft-deleted ones, which still occupy the unique constraint slot.
    existing_result = await db.execute(
        select(FlowSession).where(
            FlowSession.user_id == user_id,
            FlowSession.job_id == app.job_analysis_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing is not None:
        # Reactivate and relink the existing session.
        existing.deleted_at = None
        existing.application_id = app.id
        existing.updated_at = datetime.now(timezone.utc)
        flow = existing
    else:
        user_type = await _resolve_user_type(db)
        available_actions = _compute_actions("jd_analysis", user_type)
        flow = FlowSession(
            user_id=user_id,
            job_id=app.job_analysis_id,
            current_step="jd_analysis",
            user_type=user_type,
            available_actions=available_actions,
            application_id=app.id,
        )
        db.add(flow)
        await db.flush()  # populate flow.id

    app.flow_session_id = flow.id
    app.workflow_status = WorkflowStatus.analyzing.value


def _touch(app: Application) -> None:
    """Reset the GDPR inactivity timer on any update."""
    now = datetime.now(timezone.utc)
    app.updated_at = now
    app.expires_at = now + timedelta(days=_APPLICATION_TTL_DAYS)
