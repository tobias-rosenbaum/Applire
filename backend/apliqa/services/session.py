"""
Session service — orchestrates the interview state machine across REST calls.

Turn 1  (POST /api/session):
    [lazy gap analysis if needed] → GapDetector → QuestionGenerator → persist state → return first question

Turn N  (POST /api/session/{id}/message):
    load state → ResponseParser → ProfileUpdater → persist profile
    → if gaps remain: QuestionGenerator → return next question
    → if done: mark complete → return { complete: true }
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.models.gap import GapAnalysis
from apliqa.models.job import JobAnalysis
from apliqa.models.profile import MasterProfile
from apliqa.models.session import InterviewSession
from apliqa.providers.base import LLMProvider
from apliqa.schemas.session import (
    InterviewState,
    SessionCreateResponse,
    SessionMessageResponse,
)
from apliqa.services.gap import analyze_gaps
from apliqa.services.interview_graph import (
    gap_detector,
    profile_updater,
    question_generator_with_profile,
    response_parser,
)


# ---------------------------------------------------------------------------
# POST /api/session
# ---------------------------------------------------------------------------


async def create_session(
    job_id: uuid.UUID,
    db: AsyncSession,
    provider: LLMProvider,
) -> SessionCreateResponse:
    # Resolve job analysis
    job_result = await db.execute(
        select(JobAnalysis).where(
            JobAnalysis.id == job_id,
            JobAnalysis.deleted_at.is_(None),
        )
    )
    job = job_result.scalar_one_or_none()
    if job is None:
        raise LookupError(f"Job analysis {job_id} not found")

    # Lazy gap analysis: compute if none exists for this job
    gap_result = await db.execute(
        select(GapAnalysis)
        .where(
            GapAnalysis.job_analysis_id == job_id,
            GapAnalysis.deleted_at.is_(None),
        )
        .order_by(GapAnalysis.created_at.desc())
        .limit(1)
    )
    gap_analysis = gap_result.scalar_one_or_none()
    if gap_analysis is None:
        gap_response = await analyze_gaps(job_id, db, provider)
        # Reload as ORM model object
        gap_result2 = await db.execute(
            select(GapAnalysis).where(GapAnalysis.id == gap_response.id)
        )
        gap_analysis = gap_result2.scalar_one()

    # Resolve latest profile
    profile_result = await db.execute(
        select(MasterProfile)
        .where(MasterProfile.deleted_at.is_(None))
        .order_by(MasterProfile.created_at.desc())
        .limit(1)
    )
    profile_record = profile_result.scalar_one_or_none()
    if profile_record is None:
        raise LookupError("No profile found — import a CV first")

    # Node: GapDetector — returns ordered C-first, then B
    critical_gaps, gap_categories = gap_detector(gap_analysis)

    if not critical_gaps:
        state: InterviewState = {
            "job_id": str(job_id),
            "gap_analysis_id": str(gap_analysis.id),
            "profile_id": str(profile_record.id),
            "critical_gaps": [],
            "gap_categories": {},
            "addressed_gaps": [],
            "current_gap_index": 0,
            "current_question": "",
            "messages": [],
        }
        record = InterviewSession(
            job_analysis_id=job_id,
            gap_analysis_id=gap_analysis.id,
            profile_id=profile_record.id,
            status="complete",
            state=state,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return SessionCreateResponse(
            session_id=record.id,
            question="No critical gaps identified — your profile is a strong match!",
            gaps_total=0,
            gaps_remaining=0,
        )

    # Node: QuestionGenerator for the first gap
    first_gap = critical_gaps[0]
    first_category = gap_categories.get(first_gap)
    state = {
        "job_id": str(job_id),
        "gap_analysis_id": str(gap_analysis.id),
        "profile_id": str(profile_record.id),
        "critical_gaps": critical_gaps,
        "gap_categories": gap_categories,
        "addressed_gaps": [],
        "current_gap_index": 0,
        "current_question": "",
        "messages": [],
    }
    first_question = await question_generator_with_profile(
        state, profile_record.profile_json, provider, gap_category=first_category
    )
    state["current_question"] = first_question
    state["messages"].append({"role": "assistant", "content": first_question})

    record = InterviewSession(
        job_analysis_id=job_id,
        gap_analysis_id=gap_analysis.id,
        profile_id=profile_record.id,
        status="active",
        state=state,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return SessionCreateResponse(
        session_id=record.id,
        question=first_question,
        gaps_total=len(critical_gaps),
        gaps_remaining=len(critical_gaps),
    )


# ---------------------------------------------------------------------------
# POST /api/session/{session_id}/message
# ---------------------------------------------------------------------------


async def send_message(
    session_id: uuid.UUID,
    message: str,
    db: AsyncSession,
    provider: LLMProvider,
) -> SessionMessageResponse:
    # Load session
    session_result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.deleted_at.is_(None),
        )
    )
    record = session_result.scalar_one_or_none()
    if record is None:
        raise LookupError(f"Session {session_id} not found")
    if record.status == "complete":
        raise ValueError("Session is already complete")

    state: InterviewState = dict(record.state)

    # Append user message to history
    state["messages"].append({"role": "user", "content": message})

    current_gap = state["critical_gaps"][state["current_gap_index"]]
    current_question = state["current_question"]

    # Node: ResponseParser — extract profile data from user's answer
    patch = await response_parser(current_gap, current_question, message, provider)

    # Node: ProfileUpdater — merge into MasterProfile
    profile_record = await _load_profile(state["profile_id"], db)
    updated_profile = profile_updater(profile_record.profile_json, patch)

    # Persist profile update
    profile_record.profile_json = updated_profile
    profile_record.updated_at = datetime.now(timezone.utc)

    # Advance state
    state["addressed_gaps"] = state["addressed_gaps"] + [current_gap]
    next_index = state["current_gap_index"] + 1

    gaps_remaining = len(state["critical_gaps"]) - next_index

    if gaps_remaining <= 0 or message.strip().lower() in _DONE_SIGNALS:
        state["current_gap_index"] = next_index
        record.state = state
        record.status = "complete"
        record.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return SessionMessageResponse(complete=True)

    # Node: QuestionGenerator — generate question for the next gap
    state["current_gap_index"] = next_index
    next_gap = state["critical_gaps"][next_index]
    next_category = (state.get("gap_categories") or {}).get(next_gap)
    next_question = await question_generator_with_profile(
        state, updated_profile, provider, gap_category=next_category
    )
    state["current_question"] = next_question
    state["messages"].append({"role": "assistant", "content": next_question})

    record.state = state
    record.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return SessionMessageResponse(
        complete=False,
        question=next_question,
        gaps_remaining=gaps_remaining,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DONE_SIGNALS = {"done", "stop", "end", "quit", "exit", "fertig", "beenden"}


async def _load_profile(profile_id: str, db: AsyncSession) -> MasterProfile:
    result = await db.execute(
        select(MasterProfile).where(MasterProfile.id == uuid.UUID(profile_id))
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise LookupError(f"Profile {profile_id} not found")
    return record
