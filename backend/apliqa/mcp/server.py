"""
Apliqa MCP Server (Iteration 7, ADR 010)

Exposes the full JD → profile → gap-fill → CV tailoring workflow as MCP tools
and resources so AI agents can drive the process autonomously.

Transport: stdio (Community Edition).  SSE is reserved for Cloud Edition.

Tools:
  analyze_jd        — analyse a job description text
  get_profile       — retrieve the current MasterProfile
  update_profile    — patch a section of the MasterProfile
  analyze_gaps      — compare profile against a job
  run_interview     — start a gap-fill interview session
  send_message      — advance an active interview session
  generate_cv       — generate a tailored CV

Resources:
  profile://current       — current MasterProfile JSON
  job://{job_id}          — JobAnalysis JSON
  cv://{cv_id}            — GeneratedCV metadata JSON
"""

import json
import uuid

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from apliqa.config import settings
from apliqa.mcp.deps import get_db
from apliqa.mcp.errors import internal, invalid_input, not_found
from apliqa.models.cv import GeneratedCV
from apliqa.models.job import JobAnalysis
from apliqa.providers import get_provider
from apliqa.schemas.cv import GeneratedCVResponse
from apliqa.schemas.job import JobAnalysisResponse
from apliqa.services import cv as cv_svc
from apliqa.services import gap as gap_svc
from apliqa.services import job as job_svc
from apliqa.services import profile as profile_svc
from apliqa.services import session as session_svc

mcp = FastMCP("Apliqa")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_uuid(value: str, param: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise invalid_input(f"{param} must be a valid UUID, got: {value!r}")


# ---------------------------------------------------------------------------
# Tools (7.2 – 7.8)
# ---------------------------------------------------------------------------


@mcp.tool(description="Analyse a job description text and return a structured JobAnalysis.")
async def analyze_jd(text: str) -> dict:
    if not text.strip():
        raise invalid_input("text must not be empty")
    provider = get_provider()
    async with get_db() as db:
        try:
            result = await job_svc.analyze_jd(text.strip(), db, provider)
        except Exception as exc:
            raise internal(str(exc))
    return result.model_dump(mode="json")


@mcp.tool(description="Return the current MasterProfile.")
async def get_profile() -> dict:
    async with get_db() as db:
        result = await profile_svc.get_profile(db)
    if result is None:
        raise not_found("No profile found — import a CV first via POST /api/profile/import")
    return result.model_dump(mode="json")


@mcp.tool(
    description=(
        "Update a section of the MasterProfile. "
        "section must be one of: work_history, skills, education, languages, contact."
    )
)
async def update_profile(section: str, data: dict) -> dict:
    async with get_db() as db:
        try:
            result = await profile_svc.patch_profile_section(section, data, db)
        except ValueError as exc:
            raise invalid_input(str(exc))
        except LookupError as exc:
            raise not_found(str(exc))
    return result.model_dump(mode="json")


@mcp.tool(description="Analyse gaps between the current profile and the specified job.")
async def analyze_gaps(job_id: str) -> dict:
    jid = _parse_uuid(job_id, "job_id")
    provider = get_provider()
    async with get_db() as db:
        try:
            result = await gap_svc.analyze_gaps(jid, db, provider)
        except LookupError as exc:
            raise not_found(str(exc))
        except Exception as exc:
            raise internal(str(exc))
    return result.model_dump(mode="json")


@mcp.tool(
    description=(
        "Start a gap-fill interview session for the given job. "
        "Requires a gap analysis to exist (call analyze_gaps first). "
        "Returns session_id and the first question."
    )
)
async def run_interview(job_id: str) -> dict:
    jid = _parse_uuid(job_id, "job_id")
    provider = get_provider()
    async with get_db() as db:
        try:
            from apliqa.schemas.session import SessionCreateRequest as _SCR
            result = await session_svc.create_session(_SCR(job_id=jid), db, provider)
        except LookupError as exc:
            raise not_found(str(exc))
        except Exception as exc:
            raise internal(str(exc))
    return result.model_dump(mode="json")


@mcp.tool(
    description=(
        "Send a message in an active interview session. "
        "Returns the next question, or {complete: true} when the session is finished."
    )
)
async def send_message(session_id: str, message: str) -> dict:
    sid = _parse_uuid(session_id, "session_id")
    if not message.strip():
        raise invalid_input("message must not be empty")
    provider = get_provider()
    async with get_db() as db:
        try:
            result = await session_svc.send_message(sid, message.strip(), db, provider)
        except LookupError as exc:
            raise not_found(str(exc))
        except ValueError as exc:
            raise invalid_input(str(exc))
        except Exception as exc:
            raise internal(str(exc))
    return result.model_dump(mode="json")


@mcp.tool(
    description=(
        "Generate a tailored CV for the given job. "
        "Returns cv_id, html_url, and pdf_url. "
        "The URLs point to the FastAPI backend (APLIQA_BASE_URL)."
    )
)
async def generate_cv(job_id: str) -> dict:
    jid = _parse_uuid(job_id, "job_id")
    provider = get_provider()
    async with get_db() as db:
        try:
            result = await cv_svc.generate_cv(jid, db, provider, settings.apliqa_base_url)
        except LookupError as exc:
            raise not_found(str(exc))
        except Exception as exc:
            raise internal(str(exc))
    return result.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Resources (7.9 – 7.11)
# ---------------------------------------------------------------------------


@mcp.resource(
    "profile://current",
    mime_type="application/json",
    description="Current MasterProfile JSON.",
)
async def resource_profile() -> str:
    async with get_db() as db:
        result = await profile_svc.get_profile(db)
    if result is None:
        raise not_found("No profile found")
    return json.dumps(result.model_dump(mode="json"))


@mcp.resource(
    "job://{job_id}",
    mime_type="application/json",
    description="JobAnalysis JSON for the given job_id.",
)
async def resource_job(job_id: str) -> str:
    jid = _parse_uuid(job_id, "job_id")
    async with get_db() as db:
        result = await db.execute(
            select(JobAnalysis).where(
                JobAnalysis.id == jid,
                JobAnalysis.deleted_at.is_(None),
            )
        )
        record = result.scalar_one_or_none()
    if record is None:
        raise not_found(f"Job analysis {job_id} not found")
    return json.dumps(JobAnalysisResponse.model_validate(record).model_dump(mode="json"))


@mcp.resource(
    "cv://{cv_id}",
    mime_type="application/json",
    description="GeneratedCV metadata JSON for the given cv_id.",
)
async def resource_cv(cv_id: str) -> str:
    cid = _parse_uuid(cv_id, "cv_id")
    async with get_db() as db:
        result = await db.execute(
            select(GeneratedCV).where(
                GeneratedCV.id == cid,
                GeneratedCV.deleted_at.is_(None),
            )
        )
        record = result.scalar_one_or_none()
    if record is None:
        raise not_found(f"Generated CV {cv_id} not found")
    return json.dumps(GeneratedCVResponse.model_validate(record).model_dump(mode="json"))
