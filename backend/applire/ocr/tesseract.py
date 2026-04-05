"""Tesseract OCR backend — opt-in via OCR_BACKEND=tesseract (ADR 014).

Requires:
  - pytesseract installed in the Python environment
  - Tesseract system binary (see docker-compose.override.yml for self-hosters)
"""

import asyncio
from io import BytesIO

from applire.ocr.base import CVImageExtractor


class TesseractExtractor(CVImageExtractor):
    async def extract(self, image_bytes: bytes, mime_type: str) -> str:
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "OCR_BACKEND=tesseract requires 'pytesseract' and 'Pillow'. "
                "Install them or switch to OCR_BACKEND=mistral_vision."
            ) from exc

        image = Image.open(BytesIO(image_bytes))

        def _run() -> str:
            return pytesseract.image_to_string(image, lang="deu+eng")

        return await asyncio.get_event_loop().run_in_executor(None, _run)
