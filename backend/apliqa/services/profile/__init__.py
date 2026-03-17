import hashlib
import json
import uuid
from datetime import datetime, timezone
from io import BytesIO

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.models.profile import MasterProfile
from apliqa.models.uploads import UploadRecord
from apliqa.prompts.cv_extraction import (
    GENERIC_CV_EXTRACTION_PROMPT,
    JD_AWARE_CV_EXTRACTION_PROMPT,
    build_generic_prompt,
    build_jd_aware_prompt,
)
from apliqa.prompts.profile_extraction import SYSTEM_PROMPT, build_user_prompt
from apliqa.providers.llm.base import LLMProvider
from apliqa.services.linkedin import parse_linkedin_pdf, parse_linkedin_zip
from apliqa.services.profile.merge import merge_profiles
from apliqa.schemas.profile import (
    ConflictSummary,
    CVUploadResponse,
    EnrichmentRecord,
    FieldChange,
    MasterProfileData,
    MasterProfileResponse,
    ProfileMetadata,
)

_VALID_SECTIONS = {
    "personal_info",
    "professional_summary",
    "work_experience",
    "education",
    "certifications",
    "skills",
    "languages",
    "publications",
    "volunteer_activities",
}


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _linkedin_to_text(linkedin_json: dict) -> str:
    return json.dumps(linkedin_json, ensure_ascii=False, indent=2)


def _to_response(record: MasterProfile) -> MasterProfileResponse:
    profile_data = MasterProfileData.model_validate(record.profile_json)
    conflicts = (
        profile_data.metadata.pending_conflicts
        if profile_data.metadata
        else []
    )
    return MasterProfileResponse(
        id=record.id,
        profile=profile_data,
        completeness=profile_data.calculate_completeness(),
        merge_conflicts=conflicts,
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


def _make_enrichment_record(
    source: str,
    section: str = "*",
    action: str = "added",
    old_value: object = None,
    new_value: object = None,
    session_id: str | None = None,
    confidence: float | None = None,
) -> EnrichmentRecord:
    return EnrichmentRecord(
        timestamp=datetime.now(timezone.utc),
        source=source,
        source_session_id=session_id,
        changes=[
            FieldChange(
                section=section,
                field=section,
                action=action,
                old_value=old_value,
                new_value=new_value,
            )
        ],
        confidence=confidence,
    )


async def import_from_pdf(
    file_bytes: bytes,
    db: AsyncSession,
    provider: LLMProvider,
) -> MasterProfileResponse:
    raw_text = extract_pdf_text(file_bytes)
    if not raw_text:
        raise ValueError("Could not extract text from PDF")
    return await _import_from_text(raw_text, db, provider, created_via="cv_upload")


async def import_from_linkedin(
    linkedin_json: dict,
    db: AsyncSession,
    provider: LLMProvider,
) -> MasterProfileResponse:
    raw_text = _linkedin_to_text(linkedin_json)
    return await _import_from_text(raw_text, db, provider, created_via="linkedin_import")


async def import_from_linkedin_zip(
    zip_bytes: bytes,
    db: AsyncSession,
    provider: LLMProvider,
) -> MasterProfileResponse:
    raw_text = parse_linkedin_zip(zip_bytes)
    return await _import_from_text(raw_text, db, provider, created_via="linkedin_import")


async def import_from_linkedin_pdf(
    pdf_bytes: bytes,
    db: AsyncSession,
    provider: LLMProvider,
) -> MasterProfileResponse:
    raw_text = parse_linkedin_pdf(pdf_bytes)
    return await _import_from_text(raw_text, db, provider, created_via="linkedin_import")


async def _import_from_text(
    raw_text: str,
    db: AsyncSession,
    provider: LLMProvider,
    created_via: str = "cv_upload",
) -> MasterProfileResponse:
    data: dict = await provider.aparse_json(
        build_user_prompt(raw_text),
        system=SYSTEM_PROMPT,
        temperature=0.1,
    )
    incoming = MasterProfileData.model_validate(data)
    now = datetime.now(timezone.utc)

    existing = await _get_latest(db)
    if existing:
        existing_data = MasterProfileData.model_validate(existing.profile_json)
        merge_result = merge_profiles(existing_data, incoming, source=created_via)

        merged = merge_result.merged_profile
        enrichment = _make_enrichment_record(
            source=created_via,
            section="*",
            action="merged",
            new_value={"added": merge_result.added, "conflicts": len(merge_result.conflicts)},
        )

        if merged.metadata is None:
            merged.metadata = ProfileMetadata(
                completeness_score=merged.calculate_completeness(),
                created_via=created_via,
                created_at=existing.created_at,
                last_updated=now,
                enrichment_history=[enrichment],
                pending_conflicts=merge_result.conflicts,
            )
        else:
            merged.metadata.completeness_score = merged.calculate_completeness()
            merged.metadata.last_updated = now
            merged.metadata.enrichment_history.append(enrichment)
            # Replace pending conflicts with latest round (user resolves via endpoint)
            merged.metadata.pending_conflicts = merge_result.conflicts

        existing.profile_json = merged.model_dump(mode="json")
        existing.updated_at = now
        await db.commit()
        await db.refresh(existing)
        return _to_response(existing)

    # First import — create profile
    enrichment = _make_enrichment_record(source=created_via, action="added", new_value="initial import")
    incoming.metadata = ProfileMetadata(
        completeness_score=incoming.calculate_completeness(),
        created_via=created_via,
        created_at=now,
        last_updated=now,
        enrichment_history=[enrichment],
    )

    record = MasterProfile(profile_json=incoming.model_dump(mode="json"))
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _to_response(record)


async def get_profile(db: AsyncSession) -> MasterProfileResponse | None:
    record = await _get_latest(db)
    if not record:
        return None
    return _to_response(record)


async def patch_profile_section(
    section: str,
    value: object,
    db: AsyncSession,
    source: str = "manual_edit",
    source_session_id: str | None = None,
) -> MasterProfileResponse:
    if section not in _VALID_SECTIONS:
        raise ValueError(f"Invalid section '{section}'. Valid: {sorted(_VALID_SECTIONS)}")

    record = await _get_latest(db)
    if not record:
        raise LookupError("No profile found")

    profile_data = MasterProfileData.model_validate(record.profile_json)
    old_value = profile_data.model_dump(mode="json").get(section)

    # Apply section update
    updated_dict = profile_data.model_dump(mode="json")
    updated_dict[section] = value
    validated = MasterProfileData.model_validate(updated_dict)

    # Build enrichment record
    action = "updated" if old_value else "added"
    enrichment = _make_enrichment_record(
        source=source,
        section=section,
        action=action,
        old_value=old_value,
        new_value=value,
        session_id=source_session_id,
    )

    now = datetime.now(timezone.utc)
    if validated.metadata is None:
        validated.metadata = ProfileMetadata(
            completeness_score=validated.calculate_completeness(),
            created_via="manual",
            created_at=record.created_at,
            last_updated=now,
            enrichment_history=[enrichment],
        )
    else:
        validated.metadata.completeness_score = validated.calculate_completeness()
        validated.metadata.last_updated = now
        validated.metadata.enrichment_history.append(enrichment)

    record.profile_json = validated.model_dump(mode="json")
    record.updated_at = now
    await db.commit()
    await db.refresh(record)
    return _to_response(record)


async def get_enrichment_history(db: AsyncSession) -> list[EnrichmentRecord]:
    record = await _get_latest(db)
    if not record:
        return []
    profile_data = MasterProfileData.model_validate(record.profile_json)
    if not profile_data.metadata:
        return []
    return profile_data.metadata.enrichment_history


async def resolve_conflict(
    conflict_id: str,
    resolution: str,
    value: object,
    db: AsyncSession,
) -> MasterProfileResponse:
    """
    Resolve a pending conflict by conflict_id.

    resolution:
        "existing" — discard the incoming value, keep existing as-is
        "incoming" — accept the incoming value into the profile field
        "manual"   — write `value` into the profile field

    The conflict is marked resolved=True and removed from pending_conflicts.
    An enrichment record is appended.
    """
    record = await _get_latest(db)
    if not record:
        raise LookupError("No profile found")

    profile_data = MasterProfileData.model_validate(record.profile_json)

    if not profile_data.metadata or not profile_data.metadata.pending_conflicts:
        raise LookupError(f"Conflict '{conflict_id}' not found")

    conflict = next(
        (c for c in profile_data.metadata.pending_conflicts if c.conflict_id == conflict_id),
        None,
    )
    if conflict is None:
        raise LookupError(f"Conflict '{conflict_id}' not found")

    # Determine the winning value
    if resolution == "existing":
        chosen = conflict.existing_value
    elif resolution == "incoming":
        chosen = conflict.incoming_value
    elif resolution == "manual":
        chosen = value
    else:
        raise ValueError(f"Invalid resolution '{resolution}'. Must be existing, incoming, or manual.")

    # Apply the chosen value to the profile (only for non-list sections with a single field)
    section = conflict.section
    field_name = conflict.field
    profile_dict = profile_data.model_dump(mode="json")

    section_data = profile_dict.get(section)
    if isinstance(section_data, dict):
        section_data[field_name] = chosen
        profile_dict[section] = section_data
    # For list-type sections (work_experience etc.) date conflicts reference a specific entry;
    # we update the first matching entry. Caller may PATCH the section directly for complex edits.
    elif isinstance(section_data, list) and section == "work_experience":
        # Best effort: update the first entry that still has the old value on that field
        for entry in section_data:
            if entry.get(field_name) == conflict.existing_value:
                entry[field_name] = chosen
                break
        profile_dict[section] = section_data

    updated = MasterProfileData.model_validate(profile_dict)

    # Mark conflict resolved and rebuild pending list
    resolved_ids = {conflict_id}
    updated.metadata = profile_data.metadata.model_copy(deep=True)
    updated.metadata.pending_conflicts = [
        c.model_copy(update={"resolved": True}) if c.conflict_id in resolved_ids else c
        for c in updated.metadata.pending_conflicts
        if c.conflict_id not in resolved_ids  # remove resolved conflicts from pending
    ]

    now = datetime.now(timezone.utc)
    enrichment = _make_enrichment_record(
        source="manual_edit",
        section=section,
        action="updated",
        old_value=conflict.existing_value,
        new_value=chosen,
    )
    updated.metadata.enrichment_history.append(enrichment)
    updated.metadata.last_updated = now
    updated.metadata.completeness_score = updated.calculate_completeness()

    record.profile_json = updated.model_dump(mode="json")
    record.updated_at = now
    await db.commit()
    await db.refresh(record)
    return _to_response(record)


async def upload_cv(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    db: AsyncSession,
    provider: LLMProvider,
    storage,  # StorageProvider — imported inline to avoid circular imports
    ocr_extractor,  # CVImageExtractor
    job_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> CVUploadResponse:
    """Parse an uploaded CV file and merge it into the Master Profile (ADR 014).

    Steps:
      1. Extract raw text (format-aware, OCR fallback for scanned PDFs/images)
      2. Optionally fetch JobAnalysis context for JD-aware extraction
      3. LLM extraction → MasterProfileData
      4. Merge with existing profile (or create first profile)
      5. Persist UploadRecord (file + cost metadata)
      6. Return CVUploadResponse with status, completeness, and conflicts
    """
    from apliqa.models.job import JobAnalysis
    from apliqa.services.cv_parser import extract_text

    # 1. Text extraction
    raw_text = await extract_text(file_bytes, filename, content_type, ocr_extractor)

    # 2. JD context (optional)
    job_analysis_dict: dict | None = None
    if job_id is not None:
        result = await db.execute(
            select(JobAnalysis).where(
                JobAnalysis.id == job_id,
                JobAnalysis.deleted_at.is_(None),
            )
        )
        job_record = result.scalar_one_or_none()
        if job_record:
            job_analysis_dict = {
                "role_title": job_record.role_title,
                "required_skills": job_record.required_skills,
                "nice_to_have_skills": job_record.nice_to_have_skills,
                "keywords": job_record.keywords,
                "seniority_level": job_record.seniority_level,
                "language_requirement": job_record.language_requirement,
            }

    # 3. LLM extraction
    if job_analysis_dict:
        prompt = build_jd_aware_prompt(raw_text, job_analysis_dict)
        system = JD_AWARE_CV_EXTRACTION_PROMPT
    else:
        prompt = build_generic_prompt(raw_text)
        system = GENERIC_CV_EXTRACTION_PROMPT

    data: dict = await provider.aparse_json(prompt, system=system, temperature=0.1)
    incoming = MasterProfileData.model_validate(data)
    now = datetime.now(timezone.utc)

    # 4. Merge with existing profile (or create first profile)
    enrichment_id = uuid.uuid4()
    existing = await _get_latest(db)

    if existing:
        existing_data = MasterProfileData.model_validate(existing.profile_json)
        merge_result = merge_profiles(existing_data, incoming, source="cv_upload")
        merged = merge_result.merged_profile

        enrichment = _make_enrichment_record(
            source="cv_upload",
            section="*",
            action="merged",
            new_value={"added": merge_result.added, "conflicts": len(merge_result.conflicts)},
        )
        # Patch enrichment_id onto the record for traceability
        enrichment_id = uuid.uuid4()

        if merged.metadata is None:
            merged.metadata = ProfileMetadata(
                completeness_score=merged.calculate_completeness(),
                created_via="cv_upload",
                created_at=existing.created_at,
                last_updated=now,
                enrichment_history=[enrichment],
                pending_conflicts=merge_result.conflicts,
            )
        else:
            merged.metadata.completeness_score = merged.calculate_completeness()
            merged.metadata.last_updated = now
            merged.metadata.enrichment_history.append(enrichment)
            merged.metadata.pending_conflicts = merge_result.conflicts

        existing.profile_json = merged.model_dump(mode="json")
        existing.updated_at = now
        await db.commit()
        await db.refresh(existing)

        profile_id = existing.id
        completeness = merged.calculate_completeness()
        conflicts = merge_result.conflicts
    else:
        # First upload — create the profile
        enrichment = _make_enrichment_record(
            source="cv_upload",
            action="added",
            new_value="initial import",
        )
        incoming.metadata = ProfileMetadata(
            completeness_score=incoming.calculate_completeness(),
            created_via="cv_upload",
            created_at=now,
            last_updated=now,
            enrichment_history=[enrichment],
        )

        record = MasterProfile(profile_json=incoming.model_dump(mode="json"))
        db.add(record)
        await db.commit()
        await db.refresh(record)

        profile_id = record.id
        completeness = incoming.calculate_completeness()
        conflicts = []

    # 5. Persist file + cost metadata
    content_hash = hashlib.sha256(file_bytes).hexdigest()
    file_path = await storage.save(file_bytes, filename)

    upload_record = UploadRecord(
        user_id=user_id,
        original_filename=filename,
        content_hash=content_hash,
        mime_type=content_type,
        file_path=file_path,
        byte_size=len(file_bytes),
        llm_tokens_used=None,  # token tracking deferred — LLMProvider ABC not extended yet
        llm_provider=provider.__class__.__name__,
    )
    db.add(upload_record)
    await db.commit()

    # 6. Build response
    status = "DRAFT" if (completeness < 0.5 or bool(conflicts)) else "COMPLETE"
    conflict_summaries = [
        ConflictSummary(
            conflict_id=c.conflict_id,
            section=c.section,
            field=c.field,
            source=c.source,
        )
        for c in conflicts
    ]

    return CVUploadResponse(
        profile_id=profile_id,
        status=status,
        completeness_score=completeness,
        conflicts=conflict_summaries,
        enrichment_record_id=enrichment_id,
        expires_at=upload_record.expires_at,
    )
