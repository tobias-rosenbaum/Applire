"""StorageProvider factory — mirrors the LLMProvider / AuthProvider pattern (ADR 014)."""

from apliqa.config import settings
from apliqa.storage.base import StorageProvider


def get_storage() -> StorageProvider:
    backend = settings.storage_backend.lower()
    if backend == "local":
        from apliqa.storage.local import LocalStorageProvider

        return LocalStorageProvider(settings.upload_dir)
    raise ValueError(
        f"Unknown STORAGE_BACKEND '{backend}'. "
        "Community Edition supports: local. "
        "S3StorageProvider is available in Apliqa Cloud."
    )
