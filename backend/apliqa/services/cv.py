"""
CV service — Iteration 5

generate_cv (5.1 / 5.6):
    Load job + profile + latest gap analysis
    → LLM tailoring prompt → TailoredCVData
    → persist GeneratedCV record
    → return CVGenerateResponse

render_html (5.3 / 5.4):
    Load GeneratedCV → render Jinja2 template → return HTML string

render_pdf (5.5):
    Accept HTML string → Playwright headless Chromium → return PDF bytes
"""

import uuid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.async_api import async_playwright
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.models.cv import GeneratedCV
from apliqa.models.gap import GapAnalysis
from apliqa.models.job import JobAnalysis
from apliqa.models.profile import MasterProfile
from apliqa.prompts.cv_tailoring import SYSTEM_PROMPT, build_user_prompt
from apliqa.providers.base import LLMProvider
from apliqa.schemas.cv import CVGenerateResponse, TailoredCVData

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


# ---------------------------------------------------------------------------
# POST /api/cv/generate
# ---------------------------------------------------------------------------


async def generate_cv(
    job_id: uuid.UUID,
    db: AsyncSession,
    provider: LLMProvider,
    base_url: str,
) -> CVGenerateResponse:
    # Load job analysis
    job_result = await db.execute(
        select(JobAnalysis).where(
            JobAnalysis.id == job_id,
            JobAnalysis.deleted_at.is_(None),
        )
    )
    job = job_result.scalar_one_or_none()
    if job is None:
        raise LookupError(f"Job analysis {job_id} not found")

    # Load latest profile
    profile_result = await db.execute(
        select(MasterProfile)
        .where(MasterProfile.deleted_at.is_(None))
        .order_by(MasterProfile.created_at.desc())
        .limit(1)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise LookupError("No profile found — import a CV first")

    # Load latest gap analysis for this job (optional — used for keyword guidance)
    gap_result = await db.execute(
        select(GapAnalysis)
        .where(
            GapAnalysis.job_analysis_id == job_id,
            GapAnalysis.deleted_at.is_(None),
        )
        .order_by(GapAnalysis.created_at.desc())
        .limit(1)
    )
    gap = gap_result.scalar_one_or_none()
    keyword_gaps: list[str] = gap.keyword_gaps if gap else []
    critical_gaps: list[str] = gap.critical_gaps if gap else []

    # Build job dict for prompt
    job_dict = {
        "role_title": job.role_title,
        "required_skills": job.required_skills,
        "nice_to_have_skills": job.nice_to_have_skills,
        "keywords": job.keywords,
        "seniority_level": job.seniority_level,
        "company_culture_signals": job.company_culture_signals,
        "language_requirement": job.language_requirement,
    }

    # LLM tailoring (5.1)
    tailored_raw: dict = await provider.aparse_json(
        build_user_prompt(job_dict, profile.profile_json, keyword_gaps, critical_gaps),
        system=SYSTEM_PROMPT,
        temperature=0.3,
        max_tokens=8192,
    )

    # Validate via Pydantic (raises ValidationError on bad LLM output)
    tailored = TailoredCVData.model_validate(tailored_raw)

    # Persist (5.2)
    record = GeneratedCV(
        job_analysis_id=job.id,
        profile_id=profile.id,
        tailored_data=tailored.model_dump(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    cv_id = record.id
    return CVGenerateResponse(
        cv_id=cv_id,
        html_url=f"{base_url}/api/cv/{cv_id}/html",
        pdf_url=f"{base_url}/api/cv/{cv_id}/pdf",
    )


# ---------------------------------------------------------------------------
# GET /api/cv/{cv_id}/html  (5.4)
# ---------------------------------------------------------------------------


async def get_cv_html(cv_id: uuid.UUID, db: AsyncSession) -> str:
    record = await _load_cv(cv_id, db)
    tailored = TailoredCVData.model_validate(record.tailored_data)
    template = _jinja_env.get_template("lebenslauf.html.j2")
    return template.render(cv=tailored)


# ---------------------------------------------------------------------------
# GET /api/cv/{cv_id}/pdf  (5.5)
# ---------------------------------------------------------------------------


async def get_cv_pdf(cv_id: uuid.UUID, db: AsyncSession) -> bytes:
    html = await get_cv_html(cv_id, db)
    return await _html_to_pdf(html)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _load_cv(cv_id: uuid.UUID, db: AsyncSession) -> GeneratedCV:
    result = await db.execute(
        select(GeneratedCV).where(
            GeneratedCV.id == cv_id,
            GeneratedCV.deleted_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise LookupError(f"Generated CV {cv_id} not found")
    return record


async def _html_to_pdf(html: str) -> bytes:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        pdf_bytes = await page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        await browser.close()
    return pdf_bytes
