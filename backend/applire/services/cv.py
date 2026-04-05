"""CV service — Iteration 17 (async generation)

generate_cv (17.12 / arc42 §5.3.4):
    Create GeneratedCV record with status='pending'.
    Enqueue _render_cv_background via FastAPI BackgroundTasks.
    Return immediately — caller polls GET /api/cv/{cv_id}/status.

get_cv_status:
    Return CVStatusResponse with current status + urls if ready.

get_cv_html / get_cv_pdf:
    Load GeneratedCV (must be 'ready'), render template / PDF.
    Both raise LookupError if status != 'ready' to prevent serving stale content.

_render_cv_background:
    Heavy LLM + Playwright work — runs outside the request lifecycle.
    Updates status: pending → generating → ready | failed.
    Creates its own DB session (original request session is closed).
"""

import logging
import re
import uuid
from datetime import timezone
from pathlib import Path

from fastapi import BackgroundTasks
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.async_api import async_playwright
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.db.session import AsyncSessionLocal
from apliqa.models.cv import CVGenerationStatus, GeneratedCV
from apliqa.models.gap import GapAnalysis
from apliqa.models.job import JobAnalysis
from apliqa.models.profile import MasterProfile
from apliqa.prompts.cv_tailoring import SYSTEM_PROMPT, build_user_prompt
from apliqa.providers import get_provider
from apliqa.providers.llm.base import LLMProvider
from apliqa.schemas.cv import CVGenerateResponse, CVStatusResponse, CVTemplate, TailoredCVData

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    """Convert a role title to a URL-safe slug for use in filenames."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


_TEMPLATE_FILES: dict[str, str] = {
    "classic_german": "lebenslauf.html.j2",
    "modern_swiss": "modern_swiss.html.j2",
}

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


# ---------------------------------------------------------------------------
# POST /api/cv/generate — enqueue and return immediately
# ---------------------------------------------------------------------------


async def generate_cv(
    job_id: uuid.UUID,
    db: AsyncSession,
    provider: LLMProvider,
    background_tasks: BackgroundTasks,
    template: CVTemplate = "classic_german",
) -> CVGenerateResponse:
    """Create a pending GeneratedCV record and enqueue background rendering."""
    # Validate job exists
    job = await db.get(JobAnalysis, job_id)
    if job is None:
        raise LookupError(f"Job analysis {job_id} not found")

    # Validate profile exists
    profile_result = await db.execute(
        select(MasterProfile)
        .where(MasterProfile.deleted_at.is_(None))
        .order_by(MasterProfile.created_at.desc())
        .limit(1)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise LookupError("No profile found — import a CV first")

    # Create pending record
    record = GeneratedCV(
        job_analysis_id=job_id,
        profile_id=profile.id,
        tailored_data={},  # populated by background task
        template=template,
        status=CVGenerationStatus.pending.value,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    # Enqueue heavy work — runs after response is sent
    background_tasks.add_task(
        _render_cv_background,
        record.id,
        job_id,
        profile.id,
        template,
    )

    return CVGenerateResponse(
        cv_id=record.id,
        status=CVGenerationStatus.pending,
        expires_at=record.expires_at,
    )


# ---------------------------------------------------------------------------
# GET /api/cv/{cv_id}/status
# ---------------------------------------------------------------------------


async def get_cv_status(
    cv_id: uuid.UUID,
    db: AsyncSession,
    base_url: str,
) -> CVStatusResponse:
    from datetime import timedelta
    from datetime import datetime as _dt

    record = await _load_cv(cv_id, db)
    status = CVGenerationStatus(record.status)

    # Inline staleness check: give the frontend immediate failed feedback without
    # waiting for the daily Retention Worker run. The worker still cleans up the
    # DB record; this is belt-and-suspenders for the polling path.
    _STALE_MINUTES = 10
    if status in (CVGenerationStatus.pending, CVGenerationStatus.generating):
        cutoff = _dt.now(timezone.utc) - timedelta(minutes=_STALE_MINUTES)
        if record.created_at < cutoff:
            status = CVGenerationStatus.failed

    return CVStatusResponse(
        cv_id=record.id,
        status=status,
        html_url=f"{base_url}/api/cv/{cv_id}/html" if status == CVGenerationStatus.ready else None,
        pdf_url=f"{base_url}/api/cv/{cv_id}/pdf" if status == CVGenerationStatus.ready else None,
        error_message=record.error_message or ("Generation timed out" if status == CVGenerationStatus.failed and not record.error_message else None),
        expires_at=record.expires_at,
    )


# ---------------------------------------------------------------------------
# GET /api/jobs/{job_id}/cvs — list all CVs for a job
# ---------------------------------------------------------------------------


async def list_cvs_for_job(
    job_id: uuid.UUID,
    db: AsyncSession,
    base_url: str,
) -> list[CVStatusResponse]:
    """Return all non-deleted CVs for a job, newest first."""
    result = await db.execute(
        select(GeneratedCV)
        .where(
            GeneratedCV.job_analysis_id == job_id,
            GeneratedCV.deleted_at.is_(None),
        )
        .order_by(GeneratedCV.created_at.desc())
    )
    records = result.scalars().all()
    return [
        CVStatusResponse(
            cv_id=r.id,
            status=CVGenerationStatus(r.status),
            html_url=f"{base_url}/api/cv/{r.id}/html" if r.status == CVGenerationStatus.ready.value else None,
            pdf_url=f"{base_url}/api/cv/{r.id}/pdf" if r.status == CVGenerationStatus.ready.value else None,
            error_message=r.error_message,
            expires_at=r.expires_at,
        )
        for r in records
    ]


# ---------------------------------------------------------------------------
# PDF filename helper
# ---------------------------------------------------------------------------


async def get_pdf_filename(cv_id: uuid.UUID, db: AsyncSession) -> str:
    """Build the Content-Disposition filename for a CV PDF.

    Format: lebenslauf-{role_title_slug}-{cv_id[:8]}.pdf
    Falls back to lebenslauf-cv-{cv_id[:8]}.pdf if job not found.
    """
    record = await _load_cv_ready(cv_id, db)
    job = await db.get(JobAnalysis, record.job_analysis_id)
    role_slug = _slugify(job.role_title) if job and job.role_title else "cv"
    return f"lebenslauf-{role_slug}-{str(cv_id)[:8]}.pdf"


# ---------------------------------------------------------------------------
# GET /api/cv/{cv_id}/html  (requires status=ready)
# ---------------------------------------------------------------------------


async def get_cv_html(cv_id: uuid.UUID, db: AsyncSession) -> str:
    from apliqa.services.cv_section_editor import apply_overrides_to_tailored
    record = await _load_cv_ready(cv_id, db)
    tailored = TailoredCVData.model_validate(record.tailored_data)
    tailored = apply_overrides_to_tailored(
        tailored, record.content_snapshot, record.section_overrides
    )
    template_file = _TEMPLATE_FILES.get(record.template, "lebenslauf.html.j2")
    template = _jinja_env.get_template(template_file)
    return template.render(cv=tailored)


# ---------------------------------------------------------------------------
# GET /api/cv/{cv_id}/pdf  (requires status=ready)
# ---------------------------------------------------------------------------


async def get_cv_pdf(cv_id: uuid.UUID, db: AsyncSession) -> bytes:
    html = await get_cv_html(cv_id, db)
    return await _html_to_pdf(html)


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------


async def _render_cv_background(
    cv_id: uuid.UUID,
    job_id: uuid.UUID,
    profile_id: uuid.UUID,
    template: CVTemplate,
) -> None:
    """LLM tailoring + Playwright PDF rendering — runs outside request lifecycle.

    Opens its own DB session. Updates status: pending → generating → ready | failed.
    """
    async with AsyncSessionLocal() as db:
        record = await db.get(GeneratedCV, cv_id)
        if record is None:
            logger.error("CV %s not found in background task", cv_id)
            return

        try:
            record.status = CVGenerationStatus.generating.value
            await db.commit()

            # Load job + profile + optional gap analysis
            job = await db.get(JobAnalysis, job_id)
            profile = await db.get(MasterProfile, profile_id)

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

            job_dict = {
                "role_title": job.role_title,
                "required_skills": job.required_skills,
                "nice_to_have_skills": job.nice_to_have_skills,
                "keywords": job.keywords,
                "seniority_level": job.seniority_level,
                "company_culture_signals": job.company_culture_signals,
                "language_requirement": job.language_requirement,
            }

            provider: LLMProvider = get_provider()
            tailored_raw: dict = await provider.aparse_json(
                build_user_prompt(job_dict, profile.profile_json, keyword_gaps, critical_gaps),
                system=SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=8192,
            )

            tailored = TailoredCVData.model_validate(tailored_raw)

            from apliqa.services.cv_section_editor import build_content_snapshot
            record.content_snapshot = build_content_snapshot(tailored)

            record.tailored_data = tailored.model_dump()
            record.status = CVGenerationStatus.ready.value
            record.error_message = None
            await db.commit()

        except Exception as exc:
            logger.exception("CV generation failed for %s: %s", cv_id, exc)
            try:
                record.status = CVGenerationStatus.failed.value
                record.error_message = str(exc)[:1000]
                await db.commit()
            except Exception:
                logger.exception("Failed to persist error status for CV %s", cv_id)


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


async def _load_cv_ready(cv_id: uuid.UUID, db: AsyncSession) -> GeneratedCV:
    record = await _load_cv(cv_id, db)
    if record.status != CVGenerationStatus.ready.value:
        raise LookupError(
            f"CV {cv_id} is not ready (status: {record.status}). "
            "Poll GET /api/cv/{cv_id}/status until status='ready'."
        )
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
