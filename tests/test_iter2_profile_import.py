"""
Iteration 2 — Profile Import
Done when: Upload a real CV PDF → GET /api/profile returns a structured
           MasterProfile JSON with all major sections populated.
"""
import io
import json
from pathlib import Path

import requests

_REAL_CV_PDF = Path(__file__).parent / "files" / "Profile.pdf"

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_VALID_SECTIONS = {"work_history", "skills", "education", "languages", "contact"}


def _make_cv_pdf() -> bytes:
    """Build a minimal valid PDF (PDF 1.4) with embedded German-format CV text."""
    lines = [
        "Max Mustermann - Senior Software Engineer",
        "Email: max.mustermann@example.de | +49 89 12345678",
        "Munich, Germany | linkedin.com/in/max-mustermann",
        "BERUFSERFAHRUNG / WORK EXPERIENCE",
        "Senior Software Engineer, Acme GmbH Munich, 2021-01 bis heute",
        "  - FastAPI/Python Microservices fuer 1 Mio. Anfragen/Tag",
        "  - Migration Monolith zu Microservices; Latenz um 40% reduziert",
        "  - Fachliche Fuehrung von 3 Juniorentwicklern",
        "Software Engineer, Startup AG Berlin, 2018-06 bis 2020-12",
        "  - REST-APIs und ETL-Datenpipelines in Python entwickelt",
        "  - CI/CD-Pipelines mit GitHub Actions und Docker aufgebaut",
        "AUSBILDUNG / EDUCATION",
        "Technische Universitaet Muenchen (TUM)",
        "Bachelor of Science Informatik, 2014-2018",
        "KENNTNISSE / SKILLS",
        "Python, FastAPI, PostgreSQL, SQLAlchemy, Docker, Kubernetes, Git, Redis",
        "SPRACHEN / LANGUAGES",
        "Deutsch: Muttersprache | Englisch: C1 (fließend)",
    ]

    ops = []
    y = 740
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        ops.append(f"BT /F1 11 Tf 40 {y} Td ({safe}) Tj ET")
        y -= 16

    stream = "\n".join(ops).encode("latin-1")
    stream_len = len(stream)

    obj1 = b"<< /Type /Catalog /Pages 2 0 R >>"
    obj2 = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    obj3 = (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
        b" /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    obj4 = f"<< /Length {stream_len} >>\nstream\n".encode() + stream + b"\nendstream"
    obj5 = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    objects = [obj1, obj2, obj3, obj4, obj5]

    buf = io.BytesIO()
    buf.write(b"%PDF-1.4\n")

    offsets = []
    for i, obj_data in enumerate(objects, start=1):
        offsets.append(buf.tell())
        buf.write(f"{i} 0 obj\n".encode())
        buf.write(obj_data)
        buf.write(b"\nendobj\n")

    xref_offset = buf.tell()
    buf.write(b"xref\n")
    buf.write(f"0 {len(objects) + 1}\n".encode())
    buf.write(b"0000000000 65535 f \n")
    for offset in offsets:
        buf.write(f"{offset:010d} 00000 n \n".encode())

    buf.write(b"trailer\n")
    buf.write(f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode())
    buf.write(b"startxref\n")
    buf.write(f"{xref_offset}\n".encode())
    buf.write(b"%%EOF\n")

    return buf.getvalue()


_CV_PDF = _make_cv_pdf()

_LINKEDIN_JSON = {
    "firstName": "Anna",
    "lastName": "Beispiel",
    "emailAddress": "anna.beispiel@example.de",
    "headline": "Product Manager | SaaS | DACH",
    "location": {"name": "Hamburg, Germany"},
    "positions": [
        {
            "title": "Senior Product Manager",
            "companyName": "Munich Tech GmbH",
            "startDate": {"month": 3, "year": 2020},
            "endDate": None,
            "description": "Led B2B SaaS product roadmap; grew ARR by 60% YoY.",
        },
        {
            "title": "Business Analyst",
            "companyName": "Consulting AG",
            "startDate": {"month": 6, "year": 2017},
            "endDate": {"month": 2, "year": 2020},
            "description": "Requirements engineering and stakeholder management for automotive clients.",
        },
    ],
    "educations": [
        {
            "schoolName": "Ludwig-Maximilians-Universitaet Muenchen",
            "degreeName": "Master of Science",
            "fieldOfStudy": "Wirtschaftsinformatik",
            "startDate": {"year": 2015},
            "endDate": {"year": 2017},
        }
    ],
    "skills": [
        {"name": "Product Management"},
        {"name": "Agile / Scrum"},
        {"name": "SQL"},
        {"name": "Jira"},
        {"name": "OKR"},
    ],
    "languages": [
        {"language": {"name": "German"}, "proficiency": "NATIVE_OR_BILINGUAL"},
        {"language": {"name": "English"}, "proficiency": "PROFESSIONAL_WORKING"},
    ],
}


def _import_pdf(api: str) -> requests.Response:
    return requests.post(
        f"{api}/api/profile/import",
        files={"file": ("cv.pdf", _CV_PDF, "application/pdf")},
        timeout=90,
    )


def _import_linkedin(api: str) -> requests.Response:
    return requests.post(
        f"{api}/api/profile/import",
        data={"linkedin_json": json.dumps(_LINKEDIN_JSON)},
        timeout=90,
    )


def _get_profile(api: str) -> requests.Response:
    return requests.get(f"{api}/api/profile", timeout=10)


# ---------------------------------------------------------------------------
# PDF import tests
# ---------------------------------------------------------------------------


def test_import_pdf_returns_200(api):
    r = _import_pdf(api)
    assert r.status_code == 200, r.text


def test_import_pdf_response_structure(api):
    body = _import_pdf(api).json()

    assert isinstance(body.get("id"), str) and len(body["id"]) == 36
    assert isinstance(body.get("profile"), dict)
    assert isinstance(body.get("completeness"), int)
    assert 0 <= body["completeness"] <= 100
    assert isinstance(body.get("created_at"), str)
    assert isinstance(body.get("updated_at"), str)

    profile = body["profile"]
    assert isinstance(profile.get("work_history"), list)
    assert isinstance(profile.get("skills"), list)
    assert isinstance(profile.get("education"), list)
    assert isinstance(profile.get("languages"), list)
    assert isinstance(profile.get("contact"), dict)


def test_import_pdf_extracts_major_sections(api):
    profile = _import_pdf(api).json()["profile"]

    assert profile["work_history"], "Expected at least one work entry"
    entry = profile["work_history"][0]
    assert isinstance(entry.get("company"), str) and entry["company"]
    assert isinstance(entry.get("role"), str) and entry["role"]
    assert isinstance(entry.get("start_date"), str) and entry["start_date"]

    assert profile["skills"], "Expected at least one skill"
    assert all(isinstance(s, str) for s in profile["skills"])

    assert profile["education"], "Expected at least one education entry"
    assert profile["languages"], "Expected at least one language"

    contact = profile["contact"]
    assert isinstance(contact, dict)


# ---------------------------------------------------------------------------
# LinkedIn import tests
# ---------------------------------------------------------------------------


def test_import_linkedin_returns_200(api):
    r = _import_linkedin(api)
    assert r.status_code == 200, r.text


def test_import_linkedin_response_structure(api):
    body = _import_linkedin(api).json()

    assert isinstance(body.get("id"), str) and len(body["id"]) == 36
    profile = body["profile"]
    assert isinstance(profile.get("work_history"), list)
    assert isinstance(profile.get("skills"), list)
    assert isinstance(profile.get("education"), list)
    assert isinstance(profile.get("languages"), list)
    assert isinstance(profile.get("contact"), dict)


def test_import_linkedin_extracts_positions(api):
    profile = _import_linkedin(api).json()["profile"]

    assert len(profile["work_history"]) >= 2, "Expected both LinkedIn positions"
    companies = [e["company"] for e in profile["work_history"]]
    assert any("Munich Tech" in c or "Consulting" in c for c in companies)


# ---------------------------------------------------------------------------
# GET /api/profile tests (depends on profile having been imported above)
# ---------------------------------------------------------------------------


def test_get_profile_returns_200(api):
    _import_pdf(api)  # ensure a profile exists
    r = _get_profile(api)
    assert r.status_code == 200, r.text


def test_get_profile_structure(api):
    _import_pdf(api)
    body = _get_profile(api).json()

    assert isinstance(body.get("id"), str)
    assert isinstance(body.get("profile"), dict)
    assert isinstance(body.get("completeness"), int)
    assert 0 <= body["completeness"] <= 100


def test_get_profile_completeness_reflects_content(api):
    _import_pdf(api)
    body = _get_profile(api).json()
    # A CV with work history, skills, education, languages and contact
    # should score at least 60% (3 of 5 sections).
    assert body["completeness"] >= 60


# ---------------------------------------------------------------------------
# PATCH /api/profile/{section} tests
# ---------------------------------------------------------------------------


def test_patch_skills_returns_200(api):
    _import_pdf(api)
    r = requests.patch(
        f"{api}/api/profile/skills",
        json=["Python", "FastAPI", "PostgreSQL", "Patched via test"],
        timeout=10,
    )
    assert r.status_code == 200, r.text


def test_patch_skills_updates_value(api):
    _import_pdf(api)
    new_skills = ["TestSkill-Alpha", "TestSkill-Beta"]
    r = requests.patch(
        f"{api}/api/profile/skills",
        json=new_skills,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    updated = r.json()["profile"]["skills"]
    assert updated == new_skills


def test_patch_contact_returns_200(api):
    _import_pdf(api)
    r = requests.patch(
        f"{api}/api/profile/contact",
        json={"name": "Max Mustermann", "email": "patched@example.de", "location": "Berlin"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    contact = r.json()["profile"]["contact"]
    assert contact["email"] == "patched@example.de"


def test_patch_work_history_returns_200(api):
    _import_pdf(api)
    new_entry = {
        "company": "Test Corp",
        "role": "Test Engineer",
        "start_date": "2023-01",
        "end_date": None,
        "bullets": ["Wrote tests", "Fixed bugs"],
    }
    r = requests.patch(
        f"{api}/api/profile/work_history",
        json=[new_entry],
        timeout=10,
    )
    assert r.status_code == 200, r.text
    history = r.json()["profile"]["work_history"]
    assert len(history) == 1
    assert history[0]["company"] == "Test Corp"


# ---------------------------------------------------------------------------
# Error / validation tests
# ---------------------------------------------------------------------------


def test_import_rejects_no_input(api):
    r = requests.post(f"{api}/api/profile/import", timeout=10)
    assert r.status_code == 422


def test_import_rejects_both_inputs(api):
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("cv.pdf", _CV_PDF, "application/pdf")},
        data={"linkedin_json": json.dumps(_LINKEDIN_JSON)},
        timeout=10,
    )
    assert r.status_code == 422


def test_import_rejects_non_pdf_file(api):
    r = requests.post(
        f"{api}/api/profile/import",
        files={"file": ("cv.txt", b"not a pdf", "text/plain")},
        timeout=10,
    )
    assert r.status_code == 422


def test_import_rejects_invalid_linkedin_json(api):
    r = requests.post(
        f"{api}/api/profile/import",
        data={"linkedin_json": "this is not json {{{"},
        timeout=10,
    )
    assert r.status_code == 422


def test_patch_invalid_section_returns_422(api):
    r = requests.patch(
        f"{api}/api/profile/nonexistent_section",
        json=["anything"],
        timeout=10,
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Real LinkedIn PDF (tests/files/Profile.pdf)
# ---------------------------------------------------------------------------


def _import_real_pdf(api: str) -> requests.Response:
    pdf_bytes = _REAL_CV_PDF.read_bytes()
    return requests.post(
        f"{api}/api/profile/import",
        files={"file": ("Profile.pdf", pdf_bytes, "application/pdf")},
        timeout=90,
    )


def test_real_pdf_import_returns_200(api):
    r = _import_real_pdf(api)
    assert r.status_code == 200, r.text


def test_real_pdf_response_structure(api):
    body = _import_real_pdf(api).json()

    assert isinstance(body.get("id"), str) and len(body["id"]) == 36
    assert isinstance(body.get("completeness"), int)
    assert 0 <= body["completeness"] <= 100

    profile = body["profile"]
    assert isinstance(profile.get("work_history"), list)
    assert isinstance(profile.get("skills"), list)
    assert isinstance(profile.get("education"), list)
    assert isinstance(profile.get("languages"), list)
    assert isinstance(profile.get("contact"), dict)


def test_real_pdf_extracts_work_history(api):
    profile = _import_real_pdf(api).json()["profile"]

    assert profile["work_history"], "Expected at least one work entry from real CV"
    entry = profile["work_history"][0]
    assert isinstance(entry.get("company"), str) and entry["company"]
    assert isinstance(entry.get("role"), str) and entry["role"]
    assert isinstance(entry.get("start_date"), str) and entry["start_date"]


def test_real_pdf_extracts_skills(api):
    profile = _import_real_pdf(api).json()["profile"]
    assert profile["skills"], "Expected skills extracted from real CV"
    assert all(isinstance(s, str) for s in profile["skills"])


def test_real_pdf_completeness_high(api):
    body = _import_real_pdf(api).json()
    # A complete LinkedIn PDF should populate most sections → ≥ 80%
    assert body["completeness"] >= 80, (
        f"Completeness {body['completeness']}% is lower than expected for a full LinkedIn profile"
    )
