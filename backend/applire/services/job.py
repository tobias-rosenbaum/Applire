import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from applire.models.job import JobAnalysis
from applire.prompts.job_analysis import SYSTEM_PROMPT, build_user_prompt
from applire.providers.llm.base import LLMProvider
from applire.schemas.job import JobAnalysisResponse


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


async def analyze_jd(
    text: str,
    db: AsyncSession,
    provider: LLMProvider,
    source_url: str | None = None,
) -> JobAnalysisResponse:
    # URL-based deduplication: return existing record for the same URL.
    if source_url:
        result = await db.execute(
            select(JobAnalysis).where(JobAnalysis.source_url == source_url)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return JobAnalysisResponse.model_validate(existing)

    raw_hash = _hash_text(text)

    result = await db.execute(
        select(JobAnalysis).where(JobAnalysis.raw_text_hash == raw_hash)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return JobAnalysisResponse.model_validate(existing)

    data: dict = await provider.aparse_json(
        build_user_prompt(text),
        system=SYSTEM_PROMPT,
        temperature=0.1,
    )

    record = JobAnalysis(
        raw_text_hash=raw_hash,
        raw_text=text,
        source_url=source_url,
        company_name=data.get("company_name") or None,
        role_title=data.get("role_title", ""),
        required_skills=data.get("required_skills", []),
        nice_to_have_skills=data.get("nice_to_have_skills", []),
        keywords=data.get("keywords", []),
        seniority_level=data.get("seniority_level", ""),
        company_culture_signals=data.get("company_culture_signals", []),
        language_requirement=data.get("language_requirement") or "",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return JobAnalysisResponse.model_validate(record)
