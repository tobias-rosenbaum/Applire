"""Photo service — profile photo upload / delete / read (ADR-021).

upload_photo:  Validate, store, update personal_info.photo_url, record GDPR consent.
delete_photo:  Remove stored file, clear photo_url and consent.
get_photo:     Return raw bytes for the current user photo (GDPR portability).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from applire.models.profile import MasterProfile
from applire.models.user import User
from applire.schemas.profile import MasterProfileData
from applire.storage.base import StorageProvider

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_EXT_MAP = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


async def _get_user(user_id: uuid.UUID, db: AsyncSession) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise LookupError(f"User {user_id} not found")
    return user


async def _get_profile(db: AsyncSession) -> MasterProfile:
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


async def upload_photo(
    *,
    user_id: uuid.UUID,
    file_bytes: bytes,
    content_type: str,
    db: AsyncSession,
    storage: StorageProvider,
) -> dict[str, str]:
    """Validate, store, and record GDPR consent for a profile photo.

    Returns ``{"photo_url": str, "consent_at": str}`` on success.
    Raises ``ValueError`` for invalid format or size.
    """
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"Unsupported format '{content_type}'. Upload a JPEG, PNG, or WebP image."
        )
    if len(file_bytes) > _MAX_BYTES:
        raise ValueError("Photo exceeds the 5 MB limit. Please use a smaller file.")

    user = await _get_user(user_id, db)
    profile = await _get_profile(db)

    # Delete existing photo if present (replace path)
    profile_data = MasterProfileData.model_validate(profile.profile_json)
    if profile_data.personal_info.photo_url:
        await storage.delete(profile_data.personal_info.photo_url)

    ext = _EXT_MAP[content_type]
    path = await storage.save(file_bytes, f"photo{ext}")

    # Persist photo_url in master profile JSONB
    updated_pi = profile_data.personal_info.model_copy(update={"photo_url": path})
    profile_data = profile_data.model_copy(update={"personal_info": updated_pi})
    profile.profile_json = profile_data.model_dump(mode="json")

    # Record GDPR consent
    now = datetime.now(timezone.utc)
    user.photo_consent = True
    user.photo_consent_at = now

    await db.commit()
    return {"photo_url": path, "consent_at": now.isoformat()}


async def delete_photo(
    *,
    user_id: uuid.UUID,
    db: AsyncSession,
    storage: StorageProvider,
) -> None:
    """Remove stored photo file and clear consent. No-op if no photo on file."""
    user = await _get_user(user_id, db)
    profile = await _get_profile(db)

    profile_data = MasterProfileData.model_validate(profile.profile_json)
    if profile_data.personal_info.photo_url:
        await storage.delete(profile_data.personal_info.photo_url)
        updated_pi = profile_data.personal_info.model_copy(update={"photo_url": None})
        profile.profile_json = profile_data.model_copy(
            update={"personal_info": updated_pi}
        ).model_dump(mode="json")

    user.photo_consent = False
    user.photo_consent_at = None
    await db.commit()


async def get_photo_bytes(
    *,
    user_id: uuid.UUID,
    db: AsyncSession,
    storage: StorageProvider,
) -> bytes:
    """Return raw photo bytes for the user. Raises LookupError if no photo."""
    await _get_user(user_id, db)
    profile = await _get_profile(db)
    profile_data = MasterProfileData.model_validate(profile.profile_json)
    path = profile_data.personal_info.photo_url
    if not path:
        raise LookupError("No profile photo on file")
    return await storage.read(path)
