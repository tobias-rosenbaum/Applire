"""CVImageExtractor ABC — pluggable OCR backend (ADR 014)."""

from abc import ABC, abstractmethod


class CVImageExtractor(ABC):
    @abstractmethod
    async def extract(self, image_bytes: bytes, mime_type: str) -> str:
        """Return the raw text content of the image CV."""
