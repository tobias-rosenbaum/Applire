# Prompt version: v4
# Used by: services/interview_graph.py
#
# v4 changes vs v3 (Sprint 15):
#   - RESPONSE_PARSER_SYSTEM_PROMPT: schema extended with certifications_to_add,
#     languages_to_add, education_to_add, gap_resolution ("full"|"partial"|"none"),
#     follow_up_hint, gaps_also_addressed. gap_addressed bool replaced by gap_resolution enum.
#   - build_response_parser_prompt: accepts optional remaining_gaps list for cross-gap context
#
# v3 changes vs v2:
#   - Add GUIDED_QUESTION_SYSTEM_PROMPT for MODE B (section-building questions)
#   - Add build_guided_question_prompt() for MODE B
#   - v2 functionality unchanged
#
# v2 changes vs v1:
#   - build_question_prompt accepts an optional gap_category ("B" | "C" | None)
#   - Category B gaps produce confirmation questions ("You likely have X — can you describe it?")
#   - Category C gaps produce exploratory questions ("Tell me about your experience with X")

import json

# ---------------------------------------------------------------------------
# QuestionGenerator node — MODE A (Targeted Gap-Fill)
# ---------------------------------------------------------------------------

QUESTION_SYSTEM_PROMPT = """\
You are an expert career coach specialised in the DACH (Germany, Austria, Switzerland) job market.
Your task is to generate ONE targeted, open-ended question to help a job seeker articulate concrete \
experience that addresses a specific gap in their profile.

Requirements:
- Ask about exactly ONE aspect related to the gap
- Be encouraging and conversational in tone
- Invite specific examples: projects, companies, dates, measurable outcomes
- For CONFIRMATION questions (gap_type=B): acknowledge the likely experience and ask for specifics
- For EXPLORATORY questions (gap_type=C): ask openly about experience with the requirement
- Output ONLY the question text — no preamble, no numbering, no explanation"""


def build_question_prompt(
    gap: str,
    profile: dict,
    recent_messages: list[dict],
    gap_category: str | None = None,
) -> str:
    history = ""
    if recent_messages:
        lines = [f"{m['role'].capitalize()}: {m['content']}" for m in recent_messages[-4:]]
        history = "\n\nRecent conversation:\n" + "\n".join(lines)

    profile_summary = json.dumps(
        {
            "skills": profile.get("skills", []),
            "work_history": [
                {"company": e.get("company"), "role": e.get("role")}
                for e in profile.get("work_history", [])
            ],
        },
        ensure_ascii=False,
    )

    if gap_category == "B":
        gap_type_hint = (
            f"Gap type: CONFIRMATION (Category B) — "
            f"the system inferred the candidate likely has experience with '{gap}' "
            f"based on their profile context. Generate a confirmation question that "
            f"acknowledges this likelihood and asks for concrete specifics."
        )
    else:
        gap_type_hint = (
            f"Gap type: EXPLORATORY (Category C) — "
            f"no signal for '{gap}' was found in the profile. "
            f"Generate an open question to uncover any relevant experience."
        )

    return (
        f"Gap to address: {gap}\n"
        f"{gap_type_hint}\n\n"
        f"Candidate profile summary:\n{profile_summary}"
        f"{history}\n\n"
        "Generate the question."
    )


# ---------------------------------------------------------------------------
# QuestionGenerator node — MODE B (Guided Build)
# ---------------------------------------------------------------------------

# Section labels shown in the prompt — maps internal key to human-readable name
_SECTION_LABELS: dict[str, str] = {
    "personal_info": "Personal Information",
    "work_experience": "Work Experience",
    "education": "Education",
    "skills": "Skills",
    "languages": "Languages",
    "certifications": "Certifications",
    "professional_summary": "Professional Summary",
    "publications": "Publications",
    "volunteer_activities": "Volunteer Activities",
}

_SECTION_GUIDANCE: dict[str, str] = {
    "personal_info": (
        "Ask for the candidate's full name, location (city and country), phone number, "
        "email address, and any relevant professional profile URLs (LinkedIn, GitHub, etc.)."
    ),
    "work_experience": (
        "Ask the candidate to describe their most recent or most relevant role: "
        "company name, job title, dates, key responsibilities, and notable achievements. "
        "Encourage quantified outcomes (team size, budget, revenue impact)."
    ),
    "education": (
        "Ask about the candidate's highest or most relevant educational qualification: "
        "institution, degree, field of study, graduation year, and any notable thesis or "
        "coursework relevant to the target role."
    ),
    "skills": (
        "Ask the candidate to list their technical skills: programming languages, frameworks, "
        "tools, platforms, and methodologies. Encourage honesty about proficiency level."
    ),
    "languages": (
        "Ask which languages the candidate speaks and at what proficiency level "
        "(native, fluent, professional, basic). German and English are particularly relevant "
        "for the DACH market."
    ),
    "certifications": (
        "Ask about professional certifications, licences, or accreditations the candidate holds: "
        "name, issuing body, and year obtained."
    ),
    "professional_summary": (
        "Ask the candidate to describe their professional identity in 2–3 sentences: "
        "their core expertise, years of experience, and what type of role they are targeting."
    ),
    "publications": (
        "Ask whether the candidate has any publications, conference papers, or technical articles "
        "relevant to the role."
    ),
    "volunteer_activities": (
        "Ask whether the candidate has any volunteer work, open-source contributions, or community "
        "involvement relevant to their professional profile."
    ),
}

GUIDED_QUESTION_SYSTEM_PROMPT = """\
You are an expert career coach specialised in the DACH (Germany, Austria, Switzerland) job market.
Your task is to generate ONE warm, encouraging question to help a job seeker build their professional \
profile from scratch — section by section.

Requirements:
- Ask about exactly ONE profile section
- Be welcoming and conversational — the candidate has no existing CV to fall back on
- Invite specific, concrete details (dates, names, numbers, outcomes)
- Adapt your tone to the DACH market: professional, precise, and respectful
- Output ONLY the question text — no preamble, no numbering, no explanation"""


def build_guided_question_prompt(
    section: str,
    job_context: dict,
    recent_messages: list[dict],
) -> str:
    """Build the prompt for a MODE B (Guided Build) section question.

    section: one of _VALID_SECTIONS keys
    job_context: {"role_title": str, "seniority_level": str}
    recent_messages: last N messages from the conversation
    """
    history = ""
    if recent_messages:
        lines = [f"{m['role'].capitalize()}: {m['content']}" for m in recent_messages[-4:]]
        history = "\n\nRecent conversation:\n" + "\n".join(lines)

    label = _SECTION_LABELS.get(section, section.replace("_", " ").title())
    guidance = _SECTION_GUIDANCE.get(section, f"Ask the candidate about their {label}.")

    role_ctx = ""
    if job_context.get("role_title"):
        role_ctx = (
            f"\nTarget role context: {job_context['role_title']}"
            + (
                f" ({job_context['seniority_level']})"
                if job_context.get("seniority_level")
                else ""
            )
        )

    return (
        f"Profile section to build: {label}\n"
        f"Guidance: {guidance}"
        f"{role_ctx}"
        f"{history}\n\n"
        "Generate the question."
    )


# ---------------------------------------------------------------------------
# ResponseParser node
# ---------------------------------------------------------------------------

RESPONSE_PARSER_SYSTEM_PROMPT = """\
You are an expert career coach extracting structured profile data from a candidate's free-text answer.
Respond ONLY with a valid JSON object matching the schema below — no markdown, no explanations.

Schema:
{
  "skills_to_add": ["list of concrete skills explicitly mentioned"],
  "work_history_to_add": [
    {
      "company": "Company name or null",
      "role": "Job title or null",
      "start_date": "YYYY-MM or YYYY or null",
      "end_date": "YYYY-MM or YYYY or null (null = current)",
      "bullets": ["achievement or responsibility mentioned"]
    }
  ],
  "certifications_to_add": [
    {"name": "Certification name", "issuing_body": "Issuing body or null", "year": "YYYY or null"}
  ],
  "languages_to_add": [
    {"language": "Language name", "level": "native|fluent|professional|basic"}
  ],
  "education_to_add": [
    {
      "institution": "Institution name",
      "degree": "Degree title",
      "field": "Field of study or null",
      "graduation_year": "YYYY or null"
    }
  ],
  "gap_resolution": "full or partial or none",
  "follow_up_hint": "Short suggestion for adjacent domain to probe, or null",
  "gaps_also_addressed": ["list of other open gaps this answer also resolves"]
}

Rules:
- Only include data EXPLICITLY stated in the answer — do not infer or fabricate
- gap_resolution: "full" if the answer provides concrete, specific information about the gap;
  "partial" if relevant but incomplete or vague; "none" if off-topic or empty
- follow_up_hint: when gap_resolution is "partial" or "none", suggest a related domain or context
  the candidate might have experience in (e.g. "ask about GMP or other regulated environments").
  Set to null when gap_resolution is "full".
- gaps_also_addressed: list any other open gaps (from the provided list) that this answer also
  resolves. Empty list if none or if no list was provided.
- Omit work_history_to_add entries where role is null or empty"""


def build_response_parser_prompt(
    gap: str,
    question: str,
    answer: str,
    remaining_gaps: list[str] | None = None,
) -> str:
    other_gaps_section = ""
    if remaining_gaps:
        gaps_list = "\n".join(f"- {g}" for g in remaining_gaps)
        other_gaps_section = (
            f"\n\nOther open gaps (check if this answer also resolves any):\n{gaps_list}"
        )
    return (
        f"Gap being addressed: {gap}\n\n"
        f"Question asked: {question}\n\n"
        f"Candidate's answer: {answer}"
        f"{other_gaps_section}\n\n"
        "Extract the structured profile data."
    )
