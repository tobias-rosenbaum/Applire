"""GET/PATCH /api/settings — user preferences including default CV accent color."""
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from applire.auth import get_auth_provider
from applire.auth.base import AuthProvider
from applire.db.session import get_db
from applire.services.color_detection import _CE_STUB_USER_ID, derive_tint

router = APIRouter(prefix="/api/settings", tags=["settings"])

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class SettingsResponse(BaseModel):
    default_color_profile_id: uuid.UUID | None
    default_accent_hex: str | None


class SettingsPatchRequest(BaseModel):
    default_accent_hex: str


async def get_settings(db: AsyncSession) -> dict:
    """Service logic — returns current settings for the CE stub user."""
    from applire.models.user_settings import UserSettings
    from applire.models.color_profile import ColorProfile

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == _CE_STUB_USER_ID)
    )
    row = result.scalar_one_or_none()
    if row is None or row.default_color_profile_id is None:
        return {"default_color_profile_id": None, "default_accent_hex": None}

    cp = await db.get(ColorProfile, row.default_color_profile_id)
    if cp is None:
        return {"default_color_profile_id": None, "default_accent_hex": None}

    return {
        "default_color_profile_id": cp.id,
        "default_accent_hex": cp.seed_primary,
    }


async def update_settings(accent_hex: str, db: AsyncSession) -> dict:
    """Service logic — upsert user settings with a new default color."""
    if not _HEX_RE.match(accent_hex):
        raise ValueError(f"Invalid hex color: {accent_hex!r}. Must be #RRGGBB.")

    from applire.models.user_settings import UserSettings
    from applire.models.color_profile import ColorProfile

    derived = {"--cv-accent": accent_hex, "--cv-accent-tint": derive_tint(accent_hex)}
    cp = ColorProfile(seed_primary=accent_hex, derived=derived, source="user")
    db.add(cp)
    await db.flush()

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == _CE_STUB_USER_ID)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = UserSettings(user_id=_CE_STUB_USER_ID)
        db.add(row)
    row.default_color_profile_id = cp.id
    await db.commit()
    return {"default_color_profile_id": cp.id, "default_accent_hex": accent_hex}


@router.get("", response_model=SettingsResponse)
async def api_get_settings(
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> SettingsResponse:
    result = await get_settings(db)
    return SettingsResponse(**result)


@router.patch("", response_model=SettingsResponse)
async def api_patch_settings(
    body: SettingsPatchRequest,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> SettingsResponse:
    try:
        result = await update_settings(body.default_accent_hex, db)
        return SettingsResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
