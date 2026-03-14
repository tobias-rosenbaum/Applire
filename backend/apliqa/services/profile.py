import json
from datetime import datetime, timezone
from io import BytesIO

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.models.profile import MasterProfile
from apliqa.prompts.profile_extraction import SYSTEM_PROMPT, build_user_prompt
from apliqa.providers.base import LLMProvider
from apliqa.services.linkedin import parse_linkedin_pdf, parse_linkedin_zip
from apliqa.schemas.profile import (
    Contact,
    EducationEntry,
    Language,
    MasterProfileData,
    MasterProfileResponse,
    WorkEntry,
)

_VALID_SECTIONS = {"work_history", "skills", "education", "languages", "contact"}


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _linkedin_to_text(linkedin_json: dict) -> str:
    return json.dumps(linkedin_json, ensure_ascii=False, indent=2)


def _build_profile_data(data: dict) -> MasterProfileData:
    work_history = [
        WorkEntry(
            company=e.get("company", ""),
            role=e.get("role", ""),
            start_date=e.get("start_date", ""),
            end_date=e.get("end_date"),
            bullets=e.get("bullets", []),
        )
        for e in data.get("work_history", [])
    ]
    education = [
        EducationEntry(
            institution=e.get("institution", ""),
            degree=e.get("degree", ""),
            field=e.get("field", ""),
            start_date=e.get("start_date", ""),
            end_date=e.get("end_date"),
        )
        for e in data.get("education", [])
    ]
    languages = [
        Language(language=l.get("language", ""), level=l.get("level", ""))
        for l in data.get("languages", [])
    ]
    contact_raw = data.get("contact", {})
    contact = Contact(
        name=contact_raw.get("name", ""),
        email=contact_raw.get("email"),
        phone=contact_raw.get("phone"),
        location=contact_raw.get("location"),
        linkedin=contact_raw.get("linkedin"),
    )
    return MasterProfileData(
        work_history=work_history,
        skills=data.get("skills", []),
        education=education,
        languages=languages,
        contact=contact,
    )


def _to_response(record: MasterProfile) -> MasterProfileResponse:
    profile_data = MasterProfileData.model_validate(record.profile_json)
    return MasterProfileResponse(
        id=record.id,
        profile=profile_data,
        completeness=profile_data.calculate_completeness(),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


async def _get_latest(db: AsyncSession) -> MasterProfile | None:
    result = await db.execute(
        select(MasterProfile)
        .where(MasterProfile.deleted_at.is_(None))
        .order_by(MasterProfile.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def import_from_pdf(
    file_bytes: bytes,
    db: AsyncSession,
    provider: LLMProvider,
) -> MasterProfileResponse:
    raw_text = extract_pdf_text(file_bytes)
    if not raw_text:
        raise ValueError("Could not extract text from PDF")
    return await _import_from_text(raw_text, db, provider)


async def import_from_linkedin(
    linkedin_json: dict,
    db: AsyncSession,
    provider: LLMProvider,
) -> MasterProfileResponse:
    raw_text = _linkedin_to_text(linkedin_json)
    return await _import_from_text(raw_text, db, provider)


async def _import_from_text(
    raw_text: str,
    db: AsyncSession,
    provider: LLMProvider,
) -> MasterProfileResponse:
    data: dict = await provider.aparse_json(
        build_user_prompt(raw_text),
        system=SYSTEM_PROMPT,
        temperature=0.1,
    )
    profile_data = _build_profile_data(data)
    profile_json = profile_data.model_dump()

    existing = await _get_latest(db)
    if existing:
        existing.profile_json = profile_json
        existing.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(existing)
        return _to_response(existing)

    record = MasterProfile(profile_json=profile_json)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _to_response(record)


async def import_from_linkedin_zip(
    zip_bytes: bytes,
    db: AsyncSession,
    provider: LLMProvider,
) -> MasterProfileResponse:
    raw_text = parse_linkedin_zip(zip_bytes)
    return await _import_from_text(raw_text, db, provider)


async def import_from_linkedin_pdf(
    pdf_bytes: bytes,
    db: AsyncSession,
    provider: LLMProvider,
) -> MasterProfileResponse:
    raw_text = parse_linkedin_pdf(pdf_bytes)
    return await _import_from_text(raw_text, db, provider)


async def get_profile(db: AsyncSession) -> MasterProfileResponse | None:
    record = await _get_latest(db)
    if not record:
        return None
    return _to_response(record)


async def patch_profile_section(
    section: str,
    value: object,
    db: AsyncSession,
) -> MasterProfileResponse:
    if section not in _VALID_SECTIONS:
        raise ValueError(f"Invalid section '{section}'. Valid: {sorted(_VALID_SECTIONS)}")

    record = await _get_latest(db)
    if not record:
        raise LookupError("No profile found")

    profile_data = MasterProfileData.model_validate(record.profile_json)
    updated = profile_data.model_dump()
    updated[section] = value

    validated = MasterProfileData.model_validate(updated)
    record.profile_json = validated.model_dump()
    record.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(record)
    return _to_response(record)
