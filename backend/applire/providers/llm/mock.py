"""Mock LLM provider for CI/CD and E2E testing — no API key required.

Activated via LLM_PROVIDER=mock in .env.ci.

Detection strategy: inspects the `system` prompt to identify which service
is calling, then returns a canned schema-valid response instantly.

System prompt fingerprints:
  "HR analyst"                     → job analysis      (aparse_json)
  "CV analyst"                     → profile parsing   (aparse_json)
  "three-category gap analysis"    → gap analysis      (aparse_json)
  "extracting structured profile"  → response parser   (aparse_json)
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
    # Intentionally sparse: completeness = personal_info (0.15) + languages (0.10) = 0.25
    # This keeps user_type = "new" (threshold is 0.3) so the interview button is shown.
    "personal_info": {
        "name": "Max Mustermann",
        "email": "max.mustermann@example.com",
    },
    "work_experience": [],
    "education": [],
    "skills": [],
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

        # Fallback: return a minimal valid dict for any unrecognised prompt
        return {"mock": True, "raw_prompt_length": len(prompt)}
