"""CVImageExtractor factory — mirrors the LLMProvider / AuthProvider pattern (ADR 014)."""

from applire.ocr.base import CVImageExtractor


def get_ocr_extractor() -> CVImageExtractor:
    """Return the configured CVImageExtractor based on OCR_BACKEND env var."""
    from applire.config import settings

    backend = settings.ocr_backend.lower()
    if backend == "mistral_vision":
        from applire.ocr.mistral_vision import MistralVisionExtractor

        return MistralVisionExtractor(api_key=settings.mistral_api_key)
    if backend == "tesseract":
        from applire.ocr.tesseract import TesseractExtractor

        return TesseractExtractor()
    raise ValueError(
        f"Unknown OCR_BACKEND '{backend}'. "
        "Supported: mistral_vision (default), tesseract."
    )
