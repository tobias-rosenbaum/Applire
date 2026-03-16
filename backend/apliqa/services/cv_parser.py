"""CV parsing layer — format detection, text extraction (ADR 014, iter 12).

Supported formats: PDF (text + OCR fallback), DOCX, image (JPEG/PNG/TIFF), plain text.
PDF extraction uses pymupdf for higher fidelity than pypdf; falls back to OCR if no
text layer is present (scanned documents).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from apliqa.ocr.base import CVImageExtractor

try:
    import fitz  # pymupdf — module-level so tests can patch apliqa.services.cv_parser.fitz
except ImportError:
    fitz = None  # type: ignore[assignment]

CVFormat = Literal["pdf", "docx", "image", "text"]

_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/tiff",
    "image/bmp",
    "image/webp",
}
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}
_DOCX_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
_DOCX_EXTENSIONS = {".docx", ".doc"}

_MIN_PDF_TEXT_CHARS = 50  # below this threshold → treat as scanned, use OCR


def detect_format(filename: str, content_type: str) -> CVFormat:
    """Determine the CV format from filename extension and/or MIME type."""
    name_lower = filename.lower()
    ext = "." + name_lower.rsplit(".", 1)[-1] if "." in name_lower else ""
    mime = content_type.lower().split(";")[0].strip()

    if ext == ".pdf" or mime == "application/pdf":
        return "pdf"
    if ext in _DOCX_EXTENSIONS or mime in _DOCX_MIME_TYPES:
        return "docx"
    if ext in _IMAGE_EXTENSIONS or mime in _IMAGE_MIME_TYPES:
        return "image"
    if mime.startswith("text/") or ext in {".txt", ".md"}:
        return "text"
    # Unknown extension — let content sniffing decide at extraction time
    return "text"


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF using pymupdf.

    Returns an empty string if the PDF has no text layer (scanned).
    Caller is responsible for invoking OCR fallback when the result is empty.
    """
    if fitz is None:
        raise RuntimeError("PDF extraction requires 'pymupdf'. Add it to requirements.txt.")

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from a DOCX/DOC file using python-docx."""
    try:
        from docx import Document
        from io import BytesIO
    except ImportError as exc:
        raise RuntimeError(
            "DOCX extraction requires 'python-docx'. Add it to requirements.txt."
        ) from exc

    from io import BytesIO

    doc = Document(BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


async def extract_text(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    ocr_extractor: CVImageExtractor,
) -> str:
    """Top-level dispatcher: detect format and return extracted text.

    For PDFs with a text layer, pymupdf is used directly.
    For scanned PDFs (< _MIN_PDF_TEXT_CHARS), OCR fallback is invoked.
    """
    if not file_bytes:
        raise ValueError("Empty file — nothing to extract")

    fmt = detect_format(filename, content_type)

    if fmt == "pdf":
        text = extract_text_from_pdf(file_bytes)
        if len(text) >= _MIN_PDF_TEXT_CHARS:
            return text
        # Scanned PDF — render first page as image and run OCR
        text = await _ocr_pdf(file_bytes, ocr_extractor)
        if not text:
            raise ValueError("Could not extract text from PDF (no text layer, OCR yielded nothing)")
        return text

    if fmt == "docx":
        text = extract_text_from_docx(file_bytes)
        if not text:
            raise ValueError("Could not extract text from DOCX file")
        return text

    if fmt == "image":
        text = await ocr_extractor.extract(file_bytes, content_type)
        if not text:
            raise ValueError("OCR returned no text from image")
        return text

    # Plain text — decode as UTF-8, fall back to latin-1
    try:
        return file_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1").strip()


async def _ocr_pdf(file_bytes: bytes, ocr_extractor: CVImageExtractor) -> str:
    """Render a scanned PDF to PNG images and run OCR on each page."""
    if fitz is None:
        raise RuntimeError("pymupdf required for scanned PDF OCR")

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    texts: list[str] = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        png_bytes = pix.tobytes("png")
        page_text = await ocr_extractor.extract(png_bytes, "image/png")
        if page_text:
            texts.append(page_text)
    doc.close()
    return "\n".join(texts).strip()
