"""
LinkedIn import parsers — Iteration 9

Supports two LinkedIn export formats:

1. ZIP ("Export Data" download):
   CSVs inside the archive — Profile.csv, Positions.csv, Skills.csv, Education.csv.
   Use: parse_linkedin_zip(zip_bytes) -> str

2. PDF (LinkedIn profile page → "Save as PDF"):
   Plain-text extraction via pypdf.
   Use: parse_linkedin_pdf(pdf_bytes) -> str

Both functions return a structured plain-text blob suitable for the
_import_from_text() LLM extraction pipeline in services/profile.py.
"""

import csv
import io
import zipfile
from io import BytesIO

from pypdf import PdfReader


def parse_linkedin_zip(zip_bytes: bytes) -> str:
    """
    Parse a LinkedIn "Export Data" ZIP and return a structured plain-text
    representation suitable for LLM profile extraction.

    Raises ValueError if the ZIP is invalid or contains no usable data.
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Uploaded file is not a valid ZIP archive: {exc}") from exc

    names_lower = {n.lower(): n for n in zf.namelist()}
    sections: list[str] = []

    # ---- Profile.csv -------------------------------------------------------
    profile_key = _find(names_lower, "profile.csv")
    if profile_key:
        rows = _read_csv(zf, profile_key)
        if rows:
            r = rows[0]
            parts: list[str] = []
            name = " ".join(filter(None, [r.get("First Name", ""), r.get("Last Name", "")]))
            if name:
                parts.append(f"Name: {name}")
            if r.get("Headline"):
                parts.append(f"Headline: {r['Headline']}")
            if r.get("Location"):
                parts.append(f"Location: {r['Location']}")
            if r.get("Summary"):
                parts.append(f"Summary:\n{r['Summary']}")
            if parts:
                sections.append("=== PROFILE ===\n" + "\n".join(parts))

    # ---- Positions.csv -----------------------------------------------------
    positions_key = _find(names_lower, "positions.csv")
    if positions_key:
        rows = _read_csv(zf, positions_key)
        if rows:
            lines: list[str] = []
            for r in rows:
                title = r.get("Title", "")
                company = r.get("Company Name", "")
                started = r.get("Started On", "")
                finished = r.get("Finished On", "")
                description = r.get("Description", "")
                entry = f"- {title} at {company} ({started} – {finished or 'present'})"
                if description:
                    entry += f"\n  {description}"
                lines.append(entry)
            if lines:
                sections.append("=== WORK EXPERIENCE ===\n" + "\n".join(lines))

    # ---- Education.csv -----------------------------------------------------
    education_key = _find(names_lower, "education.csv")
    if education_key:
        rows = _read_csv(zf, education_key)
        if rows:
            lines = []
            for r in rows:
                school = r.get("School Name", "")
                degree = r.get("Degree Name", "")
                field = r.get("Field Of Study", "")
                started = r.get("Start Date", "")
                ended = r.get("End Date", "")
                parts = [school]
                if degree:
                    parts.append(degree)
                if field:
                    parts.append(field)
                date_range = f"({started} – {ended})" if started or ended else ""
                lines.append("- " + ", ".join(filter(None, parts)) + (" " + date_range if date_range else ""))
            if lines:
                sections.append("=== EDUCATION ===\n" + "\n".join(lines))

    # ---- Skills.csv --------------------------------------------------------
    skills_key = _find(names_lower, "skills.csv")
    if skills_key:
        rows = _read_csv(zf, skills_key)
        skill_names = [r.get("Name", "").strip() for r in rows if r.get("Name", "").strip()]
        if skill_names:
            sections.append("=== SKILLS ===\n" + ", ".join(skill_names))

    if not sections:
        raise ValueError(
            "LinkedIn ZIP contained no recognisable data. "
            "Expected Profile.csv, Positions.csv, Skills.csv, or Education.csv."
        )

    return "\n\n".join(sections)


def parse_linkedin_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from a LinkedIn profile PDF (downloaded via "Save to PDF"
    on the LinkedIn profile page) and return a structured plain-text
    representation suitable for LLM profile extraction.

    Raises ValueError if the PDF is unreadable or yields no text.
    """
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as exc:
        raise ValueError(f"Uploaded file is not a valid PDF: {exc}") from exc

    pages = [page.extract_text() or "" for page in reader.pages]
    raw_text = "\n".join(pages).strip()

    if not raw_text:
        raise ValueError(
            "Could not extract any text from the PDF. "
            "Make sure the file is a text-based LinkedIn profile PDF, not a scanned image."
        )

    return "=== LINKEDIN PROFILE PDF ===\n\n" + raw_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find(names_lower: dict[str, str], target: str) -> str | None:
    """Return the actual ZIP entry name for a case-insensitive target filename."""
    # Try exact filename match anywhere in the path
    for lower, original in names_lower.items():
        if lower == target or lower.endswith("/" + target):
            return original
    return None


def _read_csv(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    """Read a CSV file from the ZIP and return list of row dicts."""
    with zf.open(name) as f:
        text = f.read().decode("utf-8-sig")  # strip BOM if present
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]
