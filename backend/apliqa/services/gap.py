"""
Gap analysis service — two-pass: rule-based pre-classification + LLM refinement.

Entry points:
  analyze_gaps(job_id, db, provider)              — canonical, job-scoped
  analyze_gaps_for_session(session_id, db, provider) — session-scoped convenience wrapper

Both call the same internal _run_analysis() function.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.models.gap import GapAnalysis
from apliqa.models.job import JobAnalysis
from apliqa.models.profile import MasterProfile
from apliqa.models.session import InterviewSession
from apliqa.prompts.gap_analysis import SYSTEM_PROMPT, build_user_prompt
from apliqa.providers.base import LLMProvider
from apliqa.schemas.gap import GapAnalysisResponse
from apliqa.services.gap_inference import pre_classify


# ---------------------------------------------------------------------------
# Public: job-scoped (canonical)
# ---------------------------------------------------------------------------


async def analyze_gaps(
    job_id: uuid.UUID,
    db: AsyncSession,
    provider: LLMProvider,
) -> GapAnalysisResponse:
    """
    Canonical gap analysis entry point.

    Resolves the latest MasterProfile and runs a two-pass analysis:
      1. Rule-based pre-classification (pure Python, no LLM)
      2. LLM refinement — confirms/rejects B candidates, classifies unresolved as B or C

    Stores the result in gap_analyses and returns a GapAnalysisResponse.
    """
    job = await _resolve_job(job_id, db)
    profile = await _resolve_profile(db)
    return await _run_analysis(job, profile, db, provider)


# ---------------------------------------------------------------------------
# Public: session-scoped (convenience wrapper)
# ---------------------------------------------------------------------------


async def analyze_gaps_for_session(
    session_id: uuid.UUID,
    db: AsyncSession,
    provider: LLMProvider,
) -> GapAnalysisResponse:
    """
    Session-scoped convenience wrapper.

    Extracts the job_id from the session and delegates to analyze_gaps().
    If a GapAnalysis already exists for this job+profile it creates a new one
    (re-analysis reflects any profile changes since the last run).
    """
    session_result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.deleted_at.is_(None),
        )
    )
    session = session_result.scalar_one_or_none()
    if session is None:
        raise LookupError(f"Session {session_id} not found")

    return await analyze_gaps(session.job_analysis_id, db, provider)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


async def _run_analysis(
    job: JobAnalysis,
    profile: MasterProfile,
    db: AsyncSession,
    provider: LLMProvider,
) -> GapAnalysisResponse:
    job_dict = {
        "role_title": job.role_title,
        "required_skills": job.required_skills,
        "nice_to_have_skills": job.nice_to_have_skills,
        "keywords": job.keywords,
        "seniority_level": job.seniority_level,
        "company_culture_signals": job.company_culture_signals,
        "language_requirement": job.language_requirement,
    }

    # Pass 1: rule-based pre-classification
    pre = pre_classify(job_dict, profile.profile_json)

    # Pass 2: LLM refinement
    data: dict = await provider.aparse_json(
        build_user_prompt(job_dict, profile.profile_json, pre),
        system=SYSTEM_PROMPT,
        temperature=0.1,
    )

    record = GapAnalysis(
        job_analysis_id=job.id,
        profile_id=profile.id,
        match_score=float(data.get("match_score", 0.0)),
        critical_gaps=data.get("critical_gaps", []),
        minor_gaps=data.get("minor_gaps", []),
        strengths=data.get("strengths", []),
        keyword_gaps=data.get("keyword_gaps", []),
        category_a=data.get("category_a", []),
        category_b=data.get("category_b", []),
        category_c=data.get("category_c", []),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return GapAnalysisResponse.model_validate(record)


async def _resolve_job(job_id: uuid.UUID, db: AsyncSession) -> JobAnalysis:
    result = await db.execute(
        select(JobAnalysis).where(
            JobAnalysis.id == job_id,
            JobAnalysis.deleted_at.is_(None),
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise LookupError(f"Job analysis {job_id} not found")
    return job


async def _resolve_profile(db: AsyncSession) -> MasterProfile:
    result = await db.execute(
        select(MasterProfile)
        .where(MasterProfile.deleted_at.is_(None))
        .order_by(MasterProfile.created_at.desc())
        .limit(1)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise LookupError("No profile found — import a CV first")
    return profile
