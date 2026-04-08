"""StorageProvider ABC — pluggable file storage backend (ADR 014)."""

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    @abstractmethod
    async def save(self, file_bytes: bytes, filename: str) -> str:
        """Persist *file_bytes* and return the storage path (relative or URI)."""

    @abstractmethod
    async def delete(self, file_path: str) -> None:
        """Remove the file at *file_path*. No-op if not found."""

    @abstractmethod
    async def read(self, file_path: str) -> bytes:
        """Return the raw bytes at *file_path*. Raises FileNotFoundError if absent."""
