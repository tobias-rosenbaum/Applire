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
