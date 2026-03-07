import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.models.gap import GapAnalysis
from apliqa.models.job import JobAnalysis
from apliqa.models.profile import MasterProfile
from apliqa.prompts.gap_analysis import SYSTEM_PROMPT, build_user_prompt
from apliqa.providers.base import LLMProvider
from apliqa.schemas.gap import GapAnalysisResponse


async def analyze_gaps(
    job_id: uuid.UUID,
    db: AsyncSession,
    provider: LLMProvider,
) -> GapAnalysisResponse:
    job_result = await db.execute(
        select(JobAnalysis).where(
            JobAnalysis.id == job_id,
            JobAnalysis.deleted_at.is_(None),
        )
    )
    job = job_result.scalar_one_or_none()
    if job is None:
        raise LookupError(f"Job analysis {job_id} not found")

    profile_result = await db.execute(
        select(MasterProfile)
        .where(MasterProfile.deleted_at.is_(None))
        .order_by(MasterProfile.created_at.desc())
        .limit(1)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise LookupError("No profile found — import a CV first")

    job_dict = {
        "role_title": job.role_title,
        "required_skills": job.required_skills,
        "nice_to_have_skills": job.nice_to_have_skills,
        "keywords": job.keywords,
        "seniority_level": job.seniority_level,
        "company_culture_signals": job.company_culture_signals,
        "language_requirement": job.language_requirement,
    }

    data: dict = await provider.aparse_json(
        build_user_prompt(job_dict, profile.profile_json),
        system=SYSTEM_PROMPT,
        temperature=0.1,
    )

    record = GapAnalysis(
        job_analysis_id=job.id,
        profile_id=profile.id,
        match_score=int(data.get("match_score", 0)),
        critical_gaps=data.get("critical_gaps", []),
        minor_gaps=data.get("minor_gaps", []),
        strengths=data.get("strengths", []),
        keyword_gaps=data.get("keyword_gaps", []),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return GapAnalysisResponse.model_validate(record)
