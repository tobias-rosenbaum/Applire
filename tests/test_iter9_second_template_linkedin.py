"""
Iteration 9 — Second CV Template & LinkedIn Import (integration test)

Done when:
  - POST /api/cv/generate with { "job_id": ..., "template": "modern_swiss" }
    → GET /api/cv/{id}/html renders the Modern Swiss template (EN/DE headers,
    no "Berufserfahrung"-only headings; "Experience" is present).
  - POST /api/cv/generate without a template field defaults to "classic_german"
    (regression: existing HTML still contains "Berufserfahrung").
  - POST /api/profile/import with a LinkedIn export ZIP
    → GET /api/profile returns a populated MasterProfile (completeness > 0,
    work_history non-empty, contact.name non-empty).

Run (Docker required):
    python -m pytest tests/test_iter9_second_template_linkedin.py -v
"""
import io
import json
import zipfile
from pathlib import Path

import pytest
import requests

JD_FILE = Path(__file__).parent / "files" / "jd.txt"

_NULL_UUID = "00000000-0000-0000-0000-000000000000"

# LinkedIn fixture profile — same candidate as in iter5 so we can reuse LLM calls
_LINKEDIN = {
    "firstName": "Anna",
    "lastName": "Bauer",
    "emailAddress": "anna.bauer@example.de",
    "headline": "Senior Account Manager | Pharma & Life Sciences",
    "location": {"name": "Munich, Germany"},
    "positions": [
        {
            "title": "Senior Account Manager",
            "companyName": "Roche Deutschland GmbH",
            "startDate": {"month": 3, "year": 2020},
            "endDate": None,
            "description": (
                "Managed key accounts in the oncology division. "
                "Led cross-functional teams of 8 people. "
                "Exceeded revenue targets by 18% in FY2023."
            ),
        },
        {
            "title": "Account Manager",
            "companyName": "Novartis AG",
            "startDate": {"month": 6, "year": 2017},
            "endDate": {"month": 2, "year": 2020},
            "description": "Responsible for DACH territory sales in rare diseases.",
        },
    ],
    "educations": [
        {
            "schoolName": "Ludwig-Maximilians-Universität München",
            "degreeName": "Master of Science",
            "fieldOfStudy": "Pharmazie",
            "startDate": {"year": 2012},
            "endDate": {"year": 2017},
        }
    ],
    "skills": [
        {"name": "Veeva CRM"},
        {"name": "Salesforce"},
        {"name": "Key Account Management"},
        {"name": "DACH Sales"},
        {"name": "Oncology"},
    ],
    "languages": [
        {"language": {"name": "German"}, "proficiency": "NATIVE_OR_BILINGUAL"},
        {"language": {"name": "English"}, "proficiency": "FULL_PROFESSIONAL"},
    ],
}

# A minimal LinkedIn "Export Data" ZIP for the ZIP-upload test.
_PROFILE_CSV = (
    "First Name,Last Name,Headline,Location,Summary\r\n"
    "Lena,Müller,Software Engineer | Python & Cloud,Berlin Germany,"
    "Backend engineer with 6 years of Python and AWS experience.\r\n"
)
_POSITIONS_CSV = (
    "Title,Company Name,Description,Location,Started On,Finished On\r\n"
    "Senior Software Engineer,TechCorp GmbH,"
    "Led backend platform team. Migrated monolith to microservices. Python FastAPI.,Berlin,Jan 2021,\r\n"
    "Software Engineer,StartupXYZ AG,"
    "Developed REST APIs with Django and PostgreSQL.,Munich,Mar 2018,Dec 2020\r\n"
)
_SKILLS_CSV = (
    "Name,0\r\n"
    "Python,\r\n"
    "FastAPI,\r\n"
    "PostgreSQL,\r\n"
    "AWS,\r\n"
    "Docker,\r\n"
)


def _build_linkedin_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w") as zf:
        zf.writestr("Profile.csv", _PROFILE_CSV)
        zf.writestr("Positions.csv", _POSITIONS_CSV)
        zf.writestr("Skills.csv", _SKILLS_CSV)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _post_analyze(api: str) -> dict:
    r = requests.post(
        f"{api}/api/job/analyze",
        json={"text": JD_FILE.read_text()},
        timeout=60,
    )
    assert r.status_code == 200, f"JD analyze failed: {r.text}"
    return r.json()


def _import_profile_json(api: str) -> dict:
    r = requests.post(
        f"{api}/api/profile/import",
        data={"linkedin_json": json.dumps(_LINKEDIN)},
        timeout=90,
    )
    assert r.status_code == 200, f"Profile import failed: {r.text}"
    return r.json()


def _run_gap_analysis(api: str, job_id: str) -> None:
    r = requests.post(f"{api}/api/job/{job_id}/gaps", timeout=60)
    assert r.status_code == 200, f"Gap analysis failed: {r.text}"


def _post_generate(api: str, job_id: str, template: str | None = None) -> requests.Response:
    body: dict = {"job_id": job_id}
    if template is not None:
        body["template"] = template
    return requests.post(f"{api}/api/cv/generate", json=body, timeout=120)


def _get_html(api: str, cv_id: str) -> requests.Response:
    return requests.get(f"{api}/api/cv/{cv_id}/html", timeout=30)


# ---------------------------------------------------------------------------
# Module-scoped fixtures: one LLM call chain per test run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def job_id(api):
    return _post_analyze(api)["id"]


@pytest.fixture(scope="module")
def classic_cv(api, job_id):
    _import_profile_json(api)
    _run_gap_analysis(api, job_id)
    r = _post_generate(api, job_id, template="classic_german")
    assert r.status_code == 201, f"Classic CV generation failed: {r.text}"
    return r.json()


@pytest.fixture(scope="module")
def modern_cv(api, job_id):
    _import_profile_json(api)
    _run_gap_analysis(api, job_id)
    r = _post_generate(api, job_id, template="modern_swiss")
    assert r.status_code == 201, f"Modern Swiss CV generation failed: {r.text}"
    return r.json()


@pytest.fixture(scope="module")
def classic_html(api, classic_cv):
    r = _get_html(api, classic_cv["cv_id"])
    assert r.status_code == 200, f"GET classic html failed: {r.text}"
    return r


@pytest.fixture(scope="module")
def modern_html(api, modern_cv):
    r = _get_html(api, modern_cv["cv_id"])
    assert r.status_code == 200, f"GET modern html failed: {r.text}"
    return r


# ---------------------------------------------------------------------------
# Tests: Modern Swiss template — POST /api/cv/generate
# ---------------------------------------------------------------------------


def test_modern_swiss_generate_returns_201(api, job_id):
    _import_profile_json(api)
    _run_gap_analysis(api, job_id)
    r = _post_generate(api, job_id, template="modern_swiss")
    assert r.status_code == 201, r.text


def test_modern_swiss_response_has_urls(modern_cv):
    assert isinstance(modern_cv.get("cv_id"), str) and len(modern_cv["cv_id"]) == 36
    assert isinstance(modern_cv.get("html_url"), str) and modern_cv["html_url"]
    assert isinstance(modern_cv.get("pdf_url"), str) and modern_cv["pdf_url"]


def test_modern_swiss_html_returns_200(api, modern_cv):
    r = _get_html(api, modern_cv["cv_id"])
    assert r.status_code == 200, r.text


def test_modern_swiss_html_is_valid_document(modern_html):
    body = modern_html.text
    assert body.strip().lower().startswith("<!doctype html") or "<html" in body.lower()


def test_modern_swiss_html_contains_experience_header(modern_html):
    """Modern Swiss template uses 'Experience' (English) as the section heading."""
    assert "Experience" in modern_html.text, (
        "Modern Swiss HTML does not contain 'Experience' section heading"
    )


def test_modern_swiss_html_contains_bilingual_headers(modern_html):
    """Modern Swiss template renders both EN and DE section labels."""
    text = modern_html.text
    # At least two of the bilingual pairs must be present
    bilingual_pairs = [
        ("Experience", "Berufserfahrung"),
        ("Skills", "Kenntnisse"),
        ("Profile", "Berufliches Profil"),
        ("Education", "Ausbildung"),
        ("Languages", "Sprachkenntnisse"),
    ]
    found = sum(1 for en, de in bilingual_pairs if en in text and de in text)
    assert found >= 2, (
        f"Expected at least 2 bilingual header pairs in Modern Swiss HTML; found {found}"
    )


def test_modern_swiss_html_contains_candidate_name(modern_html):
    assert "Anna" in modern_html.text and "Bauer" in modern_html.text


def test_modern_swiss_unknown_cv_returns_404(api):
    r = _get_html(api, _NULL_UUID)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Tests: Classic German template — regression
# ---------------------------------------------------------------------------


def test_classic_german_generate_returns_201(api, job_id):
    _import_profile_json(api)
    _run_gap_analysis(api, job_id)
    r = _post_generate(api, job_id, template="classic_german")
    assert r.status_code == 201, r.text


def test_classic_german_html_contains_berufserfahrung(classic_html):
    """Classic German template must still render 'Berufserfahrung'."""
    assert "Berufserfahrung" in classic_html.text, (
        "Classic German HTML does not contain 'Berufserfahrung'"
    )


def test_classic_german_html_contains_kenntnisse(classic_html):
    assert "Kenntnisse" in classic_html.text


def test_default_template_is_classic_german(api, job_id):
    """Omitting 'template' must default to classic_german (Berufserfahrung present)."""
    _import_profile_json(api)
    _run_gap_analysis(api, job_id)
    r = _post_generate(api, job_id)  # no template param
    assert r.status_code == 201, r.text
    cv_id = r.json()["cv_id"]
    html_r = _get_html(api, cv_id)
    assert html_r.status_code == 200
    assert "Berufserfahrung" in html_r.text


def test_invalid_template_value_returns_422(api, job_id):
    r = requests.post(
        f"{api}/api/cv/generate",
        json={"job_id": job_id, "template": "nonexistent_template"},
        timeout=30,
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Tests: LinkedIn ZIP import — POST /api/profile/import
# ---------------------------------------------------------------------------


def test_linkedin_zip_import_returns_200(api):
    zip_bytes = _build_linkedin_zip()
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_export.zip", zip_bytes, "application/zip")},
        timeout=90,
    )
    assert r.status_code == 200, r.text


def test_linkedin_zip_import_returns_profile_response(api):
    zip_bytes = _build_linkedin_zip()
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_export.zip", zip_bytes, "application/zip")},
        timeout=90,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body.get("id"), str) and len(body["id"]) == 36
    assert isinstance(body.get("completeness"), int)
    assert body["completeness"] > 0


def test_linkedin_zip_profile_has_contact_name(api):
    zip_bytes = _build_linkedin_zip()
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_export.zip", zip_bytes, "application/zip")},
        timeout=90,
    )
    assert r.status_code == 200, r.text
    profile = r.json()["profile"]
    assert profile["contact"]["name"], "contact.name must be non-empty after ZIP import"


def test_linkedin_zip_profile_has_work_history(api):
    zip_bytes = _build_linkedin_zip()
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_export.zip", zip_bytes, "application/zip")},
        timeout=90,
    )
    assert r.status_code == 200, r.text
    work = r.json()["profile"]["work_history"]
    assert isinstance(work, list) and len(work) > 0, (
        "work_history must be non-empty after LinkedIn ZIP import"
    )


def test_linkedin_zip_profile_has_skills(api):
    zip_bytes = _build_linkedin_zip()
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_export.zip", zip_bytes, "application/zip")},
        timeout=90,
    )
    assert r.status_code == 200, r.text
    skills = r.json()["profile"]["skills"]
    assert isinstance(skills, list) and len(skills) > 0, (
        "skills must be non-empty after LinkedIn ZIP import"
    )


def test_linkedin_zip_get_profile_after_import(api):
    """GET /api/profile after ZIP import must return the imported data."""
    zip_bytes = _build_linkedin_zip()
    r_import = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_export.zip", zip_bytes, "application/zip")},
        timeout=90,
    )
    assert r_import.status_code == 200, r_import.text

    r_get = requests.get(f"{api}/api/profile", timeout=10)
    assert r_get.status_code == 200, r_get.text
    body = r_get.json()
    assert body["profile"]["contact"]["name"], "GET /api/profile contact.name must be set"


def test_linkedin_zip_invalid_file_returns_422(api):
    """A non-ZIP file uploaded with a .zip name must return 422."""
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("data.zip", b"this is not a zip", "application/zip")},
        timeout=10,
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Tests: LinkedIn PDF import — POST /api/profile/import
# ---------------------------------------------------------------------------


def _build_linkedin_pdf() -> bytes:
    """
    Build a minimal but valid PDF containing LinkedIn-style profile text.
    Byte offsets in the xref table are computed dynamically so the PDF
    is readable by pypdf's PdfReader.
    """
    profile_text = (
        "Lena Mueller  Software Engineer | Python and Cloud  Berlin Germany  "
        "Experience  Senior Software Engineer  TechCorp GmbH  Jan 2021 to present  "
        "Led backend platform team. Migrated monolith to microservices.  "
        "Software Engineer  StartupXYZ AG  Mar 2018 to Dec 2020  "
        "Developed REST APIs with Django and PostgreSQL.  "
        "Skills  Python  FastAPI  PostgreSQL  AWS  Docker"
    )
    # Escape PDF special chars in text
    safe = profile_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content_stream = f"BT /F1 12 Tf 50 750 Td ({safe}) Tj ET".encode()
    content_len = len(content_stream)

    # Build objects sequentially, tracking byte offsets for xref
    parts: list[bytes] = []
    offsets: list[int] = [0] * 6  # index 0 is the free entry

    header = b"%PDF-1.4\n"
    parts.append(header)
    pos = len(header)

    def add_obj(n: int, body: bytes) -> None:
        nonlocal pos
        offsets[n] = pos
        chunk = f"{n} 0 obj\n".encode() + body + b"\nendobj\n"
        parts.append(chunk)
        pos += len(chunk)

    add_obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    add_obj(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    add_obj(
        3,
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
        b" /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
    )
    add_obj(
        4,
        f"<< /Length {content_len} >>\nstream\n".encode()
        + content_stream
        + b"\nendstream",
    )
    add_obj(5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    xref_pos = pos
    xref = b"xref\n0 6\n"
    xref += b"0000000000 65535 f \n"
    for i in range(1, 6):
        xref += f"{offsets[i]:010d} 00000 n \n".encode()
    xref += (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        + b"startxref\n"
        + str(xref_pos).encode()
        + b"\n%%EOF\n"
    )
    parts.append(xref)
    return b"".join(parts)


def test_linkedin_pdf_import_returns_200(api):
    pdf_bytes = _build_linkedin_pdf()
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_profile.pdf", pdf_bytes, "application/pdf")},
        timeout=90,
    )
    assert r.status_code == 200, r.text


def test_linkedin_pdf_import_returns_profile_response(api):
    pdf_bytes = _build_linkedin_pdf()
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_profile.pdf", pdf_bytes, "application/pdf")},
        timeout=90,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body.get("id"), str) and len(body["id"]) == 36
    assert isinstance(body.get("completeness"), int)
    assert body["completeness"] > 0


def test_linkedin_pdf_profile_has_work_history(api):
    pdf_bytes = _build_linkedin_pdf()
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_profile.pdf", pdf_bytes, "application/pdf")},
        timeout=90,
    )
    assert r.status_code == 200, r.text
    work = r.json()["profile"]["work_history"]
    assert isinstance(work, list) and len(work) > 0, (
        "work_history must be non-empty after LinkedIn PDF import"
    )


def test_linkedin_pdf_profile_has_contact_name(api):
    pdf_bytes = _build_linkedin_pdf()
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_profile.pdf", pdf_bytes, "application/pdf")},
        timeout=90,
    )
    assert r.status_code == 200, r.text
    assert r.json()["profile"]["contact"]["name"], (
        "contact.name must be non-empty after LinkedIn PDF import"
    )


def test_linkedin_pdf_get_profile_after_import(api):
    """GET /api/profile after PDF import must return the imported data."""
    pdf_bytes = _build_linkedin_pdf()
    r_import = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_profile.pdf", pdf_bytes, "application/pdf")},
        timeout=90,
    )
    assert r_import.status_code == 200, r_import.text

    r_get = requests.get(f"{api}/api/profile", timeout=10)
    assert r_get.status_code == 200, r_get.text
    assert r_get.json()["profile"]["contact"]["name"], (
        "GET /api/profile contact.name must be set after PDF import"
    )


def test_linkedin_pdf_invalid_file_returns_422(api):
    """Non-PDF bytes uploaded with a .pdf name must return 422."""
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("profile.pdf", b"this is not a pdf", "application/pdf")},
        timeout=10,
    )
    assert r.status_code == 422


def test_linkedin_pdf_detection_by_content_type(api):
    """PDF upload without .pdf extension but with application/pdf content-type must be accepted."""
    pdf_bytes = _build_linkedin_pdf()
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("linkedin_export", pdf_bytes, "application/pdf")},
        timeout=90,
    )
    assert r.status_code == 200, r.text
