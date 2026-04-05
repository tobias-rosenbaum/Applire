"""Local filesystem StorageProvider — Community Edition default (ADR 014)."""

import asyncio
import uuid
from pathlib import Path

from apliqa.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    def __init__(self, upload_dir: str) -> None:
        self._base = Path(upload_dir)

    async def save(self, file_bytes: bytes, filename: str) -> str:
        """Write *file_bytes* under a UUID-prefixed name; return the relative path."""
        dest_dir = self._base
        await asyncio.get_event_loop().run_in_executor(None, dest_dir.mkdir, 0o755, True, True)

        # Preserve extension, prefix with UUID to avoid collisions
        suffix = Path(filename).suffix
        stored_name = f"{uuid.uuid4().hex}{suffix}"
        dest = dest_dir / stored_name

        def _write() -> None:
            dest.write_bytes(file_bytes)

        await asyncio.get_event_loop().run_in_executor(None, _write)
        return str(dest)

    async def delete(self, file_path: str) -> None:
        path = Path(file_path)

        def _delete() -> None:
            try:
                path.unlink()
            except FileNotFoundError:
                pass

        await asyncio.get_event_loop().run_in_executor(None, _delete)
