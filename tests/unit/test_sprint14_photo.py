"""Sprint 14 — Profile Photo Management (unit tests)

Run:
    pytest tests/unit/test_sprint14_photo.py -v
"""
import asyncio
import tempfile
from pathlib import Path

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
