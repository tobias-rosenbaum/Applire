"""Mistral Vision OCR backend — Community Edition default (ADR 014).

Uses pixtral-12b directly via the mistralai SDK.
The CVImageExtractor abstraction is vendor-independent; this implementation
calls the Mistral SDK directly because vision calls require a different model
and multimodal message format that the LLMProvider interface (ADR 009) does not
expose — that interface is intentionally minimal for text completion.
"""

import base64

from apliqa.ocr.base import CVImageExtractor

_VISION_MODEL = "pixtral-12b-2409"
_SYSTEM_PROMPT = (
    "You are a CV text extractor. Extract all text from the provided CV image "
    "exactly as it appears, preserving section structure. "
    "Return only the raw extracted text — no commentary."
)


class MistralVisionExtractor(CVImageExtractor):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def extract(self, image_bytes: bytes, mime_type: str) -> str:
        try:
            from mistralai import Mistral
        except ImportError as exc:
            raise RuntimeError(
                "Mistral Vision requires the 'mistralai' package."
            ) from exc

        b64 = base64.standard_b64encode(image_bytes).decode()
        data_uri = f"data:{mime_type};base64,{b64}"

        client = Mistral(api_key=self._api_key)
        response = await client.chat.complete_async(
            model=_VISION_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_uri}},
                        {"type": "text", "text": "Extract all text from this CV image."},
                    ],
                },
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content or ""
