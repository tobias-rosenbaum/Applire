"""Mock LLM provider for CI/CD and E2E testing — no API key required.

Activated via LLM_PROVIDER=mock in .env.ci.

Detection strategy: inspects the `system` prompt to identify which service
is calling, then returns a canned schema-valid response instantly.

System prompt fingerprints:
  "HR analyst"                     → job analysis      (aparse_json)
  "CV analyst"                     → profile parsing   (aparse_json)
  "three-category gap analysis"    → gap analysis      (aparse_json)
  "extracting structured profile"  → response parser   (aparse_json)
  "dach career consultant"         → CV tailoring      (aparse_json)
  "career coach" (acomplete)       → interview question
"""

import json
from typing import Any

from applire.providers.llm.base import LLMProvider


_JOB_ANALYSIS_RESPONSE: dict[str, Any] = {
    "company_name": "TechVision GmbH",
    "role_title": "Senior Software Engineer",
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST APIs"],
    "nice_to_have_skills": ["Kubernetes", "GraphQL", "Redis"],
    "keywords": ["backend", "microservices", "CI/CD", "agile", "DACH"],
    "seniority_level": "Senior",
    "company_culture_signals": ["agile", "remote-friendly", "innovation-driven"],
    "language_requirement": "German B2 or English fluent",
}

_PROFILE_PARSE_RESPONSE: dict[str, Any] = {
    # Rich profile: completeness = personal_info (0.15) + work_experience (0.40)
    #               + languages (0.10) = 0.65 — passes the > 0.6 upload/import assertions.
    # NOTE: _RESPONSE_PARSER_RESPONSE stays sparse so user_type stays "new" in
    #       interview tests (those go through "extracting structured profile", not here).
    "personal_info": {
        "name": "Max Mustermann",
        "email": "max.mustermann@example.com",
        "phone": "+49 170 1234567",
        "location": "Berlin, Germany",
    },
    "work_experience": [
        {
            "company": "TechVision GmbH",
            "role": "Senior Software Engineer",
            "start_date": "2021-03",
            "end_date": None,
            "description": "Backend development with Python and FastAPI.",
            "bullets": [
                "Built REST APIs serving 50k daily active users.",
                "Introduced CI/CD pipelines, reducing deploy time by 40%.",
            ],
        },
        {
            "company": "StartupX AG",
            "role": "Software Engineer",
            "start_date": "2018-06",
            "end_date": "2021-02",
            "description": "Full-stack development in an agile team.",
            "bullets": [
                "Improved test coverage from 30% to 85% using pytest.",
            ],
        },
    ],
    "education": [
        {
            "institution": "Technische Universität Berlin",
            "degree": "Master of Science",
            "field": "Computer Science",
            "start_date": "2016-10",
            "end_date": "2018-05",
        }
    ],
    "skills": [
        {"name": "Python", "category": "Technical", "proficiency": "Expert"},
        {"name": "FastAPI", "category": "Technical", "proficiency": "Advanced"},
        {"name": "PostgreSQL", "category": "Technical", "proficiency": "Advanced"},
        {"name": "Docker", "category": "Technical", "proficiency": "Intermediate"},
        {"name": "Git", "category": "Technical", "proficiency": "Advanced"},
    ],
    "languages": [
        {"language": "German", "level": "Native"},
        {"language": "English", "level": "C1"},
    ],
}

_GAP_ANALYSIS_RESPONSE: dict[str, Any] = {
    "match_score": 0.68,
    "critical_gaps": ["CI/CD pipelines", "5+ years Python experience"],
    "minor_gaps": ["Kubernetes"],
    "strengths": ["Python", "FastAPI", "PostgreSQL"],
    "keyword_gaps": ["microservices architecture"],
    "category_a": ["CI/CD pipelines"],
    "category_b": ["Kubernetes", "microservices architecture"],
    "category_c": ["5+ years Python experience"],
}

_CV_TAILORING_RESPONSE: dict[str, Any] = {
    # Valid TailoredCVData — all required fields present.
    # contact.name mirrors _PROFILE_PARSE_RESPONSE personal_info.name.
    "contact": {
        "name": "Max Mustermann",
        "email": "max.mustermann@example.com",
        "phone": "+49 170 1234567",
        "location": "Berlin, Germany",
        "linkedin": None,
    },
    "summary": (
        "Experienced software engineer with a strong background in Python and FastAPI, "
        "specialising in backend systems for the DACH market. "
        "Proven track record delivering scalable REST APIs and CI/CD pipelines."
    ),
    "work_history": [
        {
            "company": "TechVision GmbH",
            "role": "Senior Software Engineer",
            "start_date": "2021-03",
            "end_date": None,
            "bullets": [
                "Designed and implemented microservices with FastAPI and PostgreSQL.",
                "Introduced CI/CD pipelines via GitHub Actions, reducing deploy time by 40%.",
                "Led migration from monolith to containerised Docker architecture.",
            ],
        },
        {
            "company": "StartupX AG",
            "role": "Software Engineer",
            "start_date": "2018-06",
            "end_date": "2021-02",
            "bullets": [
                "Built REST APIs serving 50k daily active users.",
                "Improved test coverage from 30% to 85% using pytest.",
            ],
        },
    ],
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST APIs", "CI/CD", "Git"],
    "education": [
        {
            "institution": "Technische Universität Berlin",
            "degree": "Master of Science",
            "field": "Computer Science",
            "start_date": "2016-10",
            "end_date": "2018-05",
        }
    ],
    "languages": [
        {"language": "German", "level": "Native"},
        {"language": "English", "level": "C1"},
    ],
}

_RESPONSE_PARSER_RESPONSE: dict[str, Any] = {
    # Empty skills_to_add keeps profile completeness below the 0.3 threshold so
    # user_type stays "new" and the interview button remains visible across all tests.
    "skills_to_add": [],
    "work_history_to_add": [],
    "gap_addressed": True,
}

_INTERVIEW_QUESTION = (
    "Can you describe a specific project where you implemented CI/CD pipelines "
    "and explain the tools and processes you used?"
)


class MockLLMProvider(LLMProvider):
    """Instant, deterministic LLM provider for CI/CD and E2E tests.

    Returns canned schema-valid responses without any network call.
    Identifies the calling service from the system prompt fingerprint.
    """

    async def acomplete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        return _INTERVIEW_QUESTION

    async def aparse_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        system_lower = (system or "").lower()

        if "hr analyst" in system_lower:
            return dict(_JOB_ANALYSIS_RESPONSE)

        if "cv analyst" in system_lower:
            return dict(_PROFILE_PARSE_RESPONSE)

        if "three-category gap analysis" in system_lower or "gap analysis" in system_lower:
            return dict(_GAP_ANALYSIS_RESPONSE)

        if "extracting structured profile" in system_lower:
            return dict(_RESPONSE_PARSER_RESPONSE)

        if "dach career consultant" in system_lower:
            return dict(_CV_TAILORING_RESPONSE)

        # Fallback: return a minimal valid dict for any unrecognised prompt
        return {"mock": True, "raw_prompt_length": len(prompt)}
