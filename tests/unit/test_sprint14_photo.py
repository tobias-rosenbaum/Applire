"""Sprint 14 — Profile Photo Management (unit tests)

Run:
    pytest tests/unit/test_sprint14_photo.py -v
"""
import tempfile

import pytest


# ---------------------------------------------------------------------------
# Task 1 — StorageProvider.read()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_local_storage_read_returns_saved_bytes():
    """read() returns exactly the bytes that were previously saved."""
    from applire.storage.local import LocalStorageProvider

    with tempfile.TemporaryDirectory() as tmp:
        storage = LocalStorageProvider(tmp)
        data = b"fake-jpeg-bytes"
        path = await storage.save(data, "photo.jpg")

        result = await storage.read(path)

        assert result == data


@pytest.mark.asyncio
async def test_local_storage_read_raises_for_missing_file():
    """read() raises FileNotFoundError when the path does not exist."""
    from applire.storage.local import LocalStorageProvider

    with tempfile.TemporaryDirectory() as tmp:
        storage = LocalStorageProvider(tmp)

        with pytest.raises(FileNotFoundError):
            await storage.read(f"{tmp}/does_not_exist.jpg")


def test_user_photo_consent_defaults():
    from applire.models.user import User
    user = User()
    assert user.photo_consent is False
    assert user.photo_consent_at is None


# ---------------------------------------------------------------------------
# Task 3 — TailoredCVData schema
# ---------------------------------------------------------------------------

def test_tailored_contact_has_photo_url():
    """TailoredContact accepts photo_url and defaults to None."""
    from applire.schemas.cv import TailoredContact

    c = TailoredContact(name="Anna Bauer")
    assert c.photo_url is None

    c2 = TailoredContact(name="Anna Bauer", photo_url="/uploads/photo.jpg")
    assert c2.photo_url == "/uploads/photo.jpg"


def test_tailored_cv_data_has_show_photo():
    """TailoredCVData.show_photo defaults to True."""
    from applire.schemas.cv import TailoredCVData, TailoredContact

    cv = TailoredCVData(contact=TailoredContact(name="Anna"))
    assert cv.show_photo is True

    cv2 = TailoredCVData(contact=TailoredContact(name="Anna"), show_photo=False)
    assert cv2.show_photo is False


# ---------------------------------------------------------------------------
# Task 4 — Photo service
# ---------------------------------------------------------------------------

import uuid as _uuid
from datetime import datetime, timezone

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def photo_db():
    """In-memory SQLite session with all applire tables."""
    from applire.db.session import Base
    # Import ALL models so Base.metadata knows about every table (FK resolution).
    import applire.models.user  # noqa: F401
    import applire.models.profile  # noqa: F401
    import applire.models.job  # noqa: F401
    import applire.models.gap  # noqa: F401
    import applire.models.cv  # noqa: F401
    import applire.models.session  # noqa: F401
    import applire.models.flow  # noqa: F401
    import applire.models.uploads  # noqa: F401
    import applire.models.application  # noqa: F401

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_upload_photo_stores_file_and_sets_photo_url(photo_db):
    """upload_photo() saves bytes, sets personal_info.photo_url, sets photo_consent."""
    from applire.models.user import User
    from applire.models.profile import MasterProfile
    from applire.schemas.profile import MasterProfileData, PersonalInfo

    user_id = _uuid.uuid4()
    user = User(id=user_id, email="anna@example.de")
    photo_db.add(user)

    profile = MasterProfile(
        profile_json=MasterProfileData(
            personal_info=PersonalInfo(name="Anna Bauer")
        ).model_dump(mode="json"),
    )
    photo_db.add(profile)
    await photo_db.commit()

    with tempfile.TemporaryDirectory() as tmp:
        from applire.storage.local import LocalStorageProvider
        storage = LocalStorageProvider(tmp)

        from applire.services.photo import upload_photo
        result = await upload_photo(
            user_id=user_id,
            file_bytes=b"fake-jpeg",
            content_type="image/jpeg",
            db=photo_db,
            storage=storage,
        )

    assert result["photo_url"] is not None
    assert result["consent_at"] is not None

    await photo_db.refresh(user)
    assert user.photo_consent is True
    assert user.photo_consent_at is not None

    await photo_db.refresh(profile)
    from applire.schemas.profile import MasterProfileData
    profile_data = MasterProfileData.model_validate(profile.profile_json)
    assert profile_data.personal_info.photo_url == result["photo_url"]


@pytest.mark.asyncio
async def test_delete_photo_clears_url_and_consent(photo_db):
    """delete_photo() removes the file, clears photo_url, clears consent."""
    from applire.models.user import User
    from applire.models.profile import MasterProfile
    from applire.schemas.profile import MasterProfileData, PersonalInfo

    user_id = _uuid.uuid4()
    user = User(
        id=user_id, email="anna2@example.de",
        photo_consent=True,
        photo_consent_at=datetime.now(timezone.utc),
    )
    photo_db.add(user)

    with tempfile.TemporaryDirectory() as tmp:
        from applire.storage.local import LocalStorageProvider
        storage = LocalStorageProvider(tmp)

        # Pre-save a file so delete has something to remove
        path = await storage.save(b"fake-jpeg", "photo.jpg")

        profile = MasterProfile(
            profile_json=MasterProfileData(
                personal_info=PersonalInfo(name="Anna Bauer", photo_url=path)
            ).model_dump(mode="json"),
        )
        photo_db.add(profile)
        await photo_db.commit()

        from applire.services.photo import delete_photo
        await delete_photo(user_id=user_id, db=photo_db, storage=storage)

    await photo_db.refresh(user)
    assert user.photo_consent is False
    assert user.photo_consent_at is None

    await photo_db.refresh(profile)
    profile_data = MasterProfileData.model_validate(profile.profile_json)
    assert profile_data.personal_info.photo_url is None


# ---------------------------------------------------------------------------
# Task 6 — Merge service photo_url gap-fill
# ---------------------------------------------------------------------------

def test_merge_gap_fills_photo_url():
    """Merge fills photo_url if existing is empty but incoming has a value."""
    from applire.schemas.profile import MasterProfileData, PersonalInfo
    from applire.services.profile.merge import merge_profiles

    existing = MasterProfileData(
        personal_info=PersonalInfo(name="Anna", photo_url=None)
    )
    incoming = MasterProfileData(
        personal_info=PersonalInfo(name="Anna", photo_url="/uploads/photo.jpg")
    )
    result = merge_profiles(existing, incoming, source="test")
    assert result.merged_profile.personal_info.photo_url == "/uploads/photo.jpg"


def test_merge_does_not_overwrite_existing_photo_url():
    """Merge never overwrites a user-set photo_url with incoming data."""
    from applire.schemas.profile import MasterProfileData, PersonalInfo
    from applire.services.profile.merge import merge_profiles

    existing = MasterProfileData(
        personal_info=PersonalInfo(name="Anna", photo_url="/uploads/my_photo.jpg")
    )
    incoming = MasterProfileData(
        personal_info=PersonalInfo(name="Anna", photo_url="/uploads/other_photo.jpg")
    )
    result = merge_profiles(existing, incoming, source="test")
    # photo_url is user-managed, not LLM-extracted — never overwrite
    assert result.merged_profile.personal_info.photo_url == "/uploads/my_photo.jpg"
    assert result.conflicts == [], "photo_url conflict must never be raised — it is user-managed"
