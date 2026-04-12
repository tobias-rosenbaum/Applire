"""PATCH /api/cv/{cv_id}/color — apply a user accent color override to a generated CV."""
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from applire.auth import get_auth_provider
from applire.auth.base import AuthProvider
from applire.db.session import get_db
from applire.models.color_profile import ColorProfile
from applire.models.cv import CVGenerationStatus, GeneratedCV
from applire.services.color_detection import derive_tint

router = APIRouter(prefix="/api/cv", tags=["cv"])

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class ColorOverrideRequest(BaseModel):
    accent_hex: str


class ColorOverrideResponse(BaseModel):
    color_profile_id: uuid.UUID
    derived: dict


async def apply_cv_color(
    cv_id: uuid.UUID,
    accent_hex: str,
    db: AsyncSession,
) -> dict:
    """Service logic — extracted for unit testability."""
    if not _HEX_RE.match(accent_hex):
        raise ValueError(f"Invalid hex color: {accent_hex!r}. Must be #RRGGBB.")

    from sqlalchemy import select
    result = await db.execute(
        select(GeneratedCV).where(
            GeneratedCV.id == cv_id,
            GeneratedCV.deleted_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise LookupError(f"CV {cv_id} not found")
    if record.status != CVGenerationStatus.ready.value:
        raise LookupError(f"CV {cv_id} is not ready (status={record.status})")

    derived = {"--cv-accent": accent_hex, "--cv-accent-tint": derive_tint(accent_hex)}
    cp = ColorProfile(seed_primary=accent_hex, derived=derived, source="user")
    db.add(cp)
    await db.flush()

    record.color_profile_id = cp.id
    await db.commit()
    await db.refresh(cp)

    return {"color_profile_id": cp.id, "derived": derived}


@router.patch("/{cv_id}/color", response_model=ColorOverrideResponse)
async def patch_cv_color(
    cv_id: uuid.UUID,
    body: ColorOverrideRequest,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> ColorOverrideResponse:
    try:
        result = await apply_cv_color(cv_id, body.accent_hex, db)
        return ColorOverrideResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
