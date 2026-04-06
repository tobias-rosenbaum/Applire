# Prompt version: v1
# Used by: services/profile/__init__.py → upload_cv() → LLMProvider.aparse_json
#
# Two variants (ADR 014):
#   GENERIC_CV_EXTRACTION_PROMPT  — no JD context; general-purpose profile extraction
#   JD_AWARE_CV_EXTRACTION_PROMPT — injects JobAnalysis context for relevance-weighted extraction
#
# Both variants target the full MasterProfileData schema (iter 11).
# The model_validator on MasterProfileData handles backwards-compat with older field names.

_SCHEMA_DESCRIPTION = """\
{
  "personal_info": {
    "name": "Full name",
    "email": "Email address or null",
    "phone": "Phone number or null",
    "location": "City / region or null",
    "address": "Street address or null",
    "nationality": "Nationality or null",
    "date_of_birth": "ISO date YYYY-MM-DD or null",
    "linkedin_url": "LinkedIn profile URL or null",
    "xing_url": "XING profile URL or null",
    "website_url": "Personal website URL or null"
  },
  "professional_summary": {
    "de": "German-language professional summary or null",
    "en": "English-language professional summary or null"
  },
  "work_experience": [
    {
      "company": "Employer name",
      "role": "Primary job title",
      "role_aliases": ["Any additional titles used for this position"],
      "location": "Office city/country or null",
      "start_date": "e.g. '2020-01' or '2020' — partial dates accepted",
      "end_date": "e.g. '2023-06' or null for current position",
      "responsibilities": ["Responsibility bullet points"],
      "achievements": ["Achievement bullet points with metrics where stated"],
      "technologies": ["Tools, languages, frameworks mentioned"],
      "industry_context": "Industry or domain context or null",
      "team_size": "Integer team size or null",
      "budget_managed": "Budget amount as string or null"
    }
  ],
  "education": [
    {
      "institution": "University or school name",
      "degree": "Degree type e.g. 'Bachelor of Science', 'Master', 'Ausbildung'",
      "field": "Field of study or specialisation",
      "start_date": "e.g. '2015' or null",
      "end_date": "e.g. '2018' or null",
      "grade": "Final grade or GPA as string or null",
      "thesis_title": "Thesis or dissertation title or null",
      "relevant_coursework": ["Relevant courses if listed"]
    }
  ],
  "certifications": [
    {
      "name": "Certification name",
      "issuing_organization": "Issuing body",
      "date_obtained": "ISO date YYYY-MM-DD or null",
      "expiry_date": "ISO date YYYY-MM-DD or null",
      "credential_id": "Credential ID or null",
      "credential_url": "Verification URL or null"
    }
  ],
  "skills": [
    {
      "name": "Skill name",
      "category": "technical | soft | language | domain",
      "proficiency": "basic | intermediate | advanced | expert",
      "years_experience": "Integer years or null",
      "last_used": "ISO date YYYY-MM-DD or null"
    }
  ],
  "languages": [
    {
      "language": "Language name e.g. 'German', 'English'",
      "level": "Proficiency e.g. 'Native', 'C1', 'B2', 'Fluent', 'Business fluent'"
    }
  ],
  "publications": [
    {
      "title": "Publication or patent title",
      "type": "publication | patent",
      "co_authors": ["Co-author names"],
      "venue": "Journal, conference, or patent office or null",
      "published_date": "ISO date YYYY-MM-DD or null",
      "doi": "DOI string or null",
      "url": "URL or null",
      "patent_number": "Patent number or null"
    }
  ],
  "volunteer_activities": [
    {
      "role": "Volunteer role title",
      "organization": "Organisation name",
      "location": "City/country or null",
      "start_date": "ISO date YYYY-MM-DD or null",
      "end_date": "ISO date YYYY-MM-DD or null",
      "description": "Activity description or null",
      "cause": "Cause area e.g. 'Education', 'Environment' or null"
    }
  ]
}"""

_SYSTEM_BASE = """\
You are an expert CV analyst specialised in the DACH (Germany, Austria, Switzerland) job market.
Extract structured profile information from the provided CV text and return it as a single JSON object.
Respond ONLY with valid JSON — no markdown fences, no commentary, no explanations.

Rules:
- Extract everything stated or clearly implied; do not invent data.
- Separate responsibilities (day-to-day duties) from achievements (outcomes with metrics) into their respective lists.
- For technology stacks, extract individual tools/languages/frameworks into the technologies list.
- Preserve German umlauts and special characters exactly as written.
- Use null for missing optional fields — never omit required fields.
- For DACH CVs: Ausbildung maps to education; Praktikum/Werkstudent map to work_experience entries.

Output schema:
""" + _SCHEMA_DESCRIPTION

GENERIC_CV_EXTRACTION_PROMPT = _SYSTEM_BASE

JD_AWARE_CV_EXTRACTION_PROMPT = (
    _SYSTEM_BASE
    + """

JD-aware extraction instructions:
You have been provided with a job description analysis below. Use it to:
- Prioritise extracting technologies and skills that are relevant to the target role.
- Write responsibilities and achievements using language that maps naturally to the JD requirements.
- Assign higher proficiency values to skills that directly match the JD's required or preferred skills.
- Do NOT invent experience that is absent from the CV — only re-emphasise what is present.
"""
)


def build_generic_prompt(raw_text: str) -> str:
    """Return the user message string for generic CV extraction.

    Pass to LLMProvider.aparse_json(prompt, system=GENERIC_CV_EXTRACTION_PROMPT).
    """
    return (
        "Extract the structured profile from the following CV text and return the JSON:\n\n"
        + raw_text
    )


def build_jd_aware_prompt(raw_text: str, job_analysis: dict) -> str:
    """Return the user message string for JD-context-aware CV extraction.

    Pass to LLMProvider.aparse_json(prompt, system=JD_AWARE_CV_EXTRACTION_PROMPT).

    *job_analysis* is the serialisable dict from a JobAnalysis DB record.
    The LLM is instructed not to invent data absent from the CV.
    """
    import json

    jd_context = json.dumps(job_analysis, ensure_ascii=False, indent=2)
    return (
        "Job Description Analysis (for context only — do not invent data):\n"
        + jd_context
        + "\n\nExtract the structured profile from the following CV text and return the JSON:\n\n"
        + raw_text
    )
