"""StorageProvider factory — mirrors the LLMProvider / AuthProvider pattern (ADR 014)."""

from applire.config import settings
from applire.storage.base import StorageProvider


def get_storage() -> StorageProvider:
    backend = settings.storage_backend.lower()
    if backend == "local":
        from applire.storage.local import LocalStorageProvider

        return LocalStorageProvider(settings.upload_dir)
    raise ValueError(
        f"Unknown STORAGE_BACKEND '{backend}'. "
        "Community Edition supports: local. "
        "S3StorageProvider is available in Applire Cloud."
    )
