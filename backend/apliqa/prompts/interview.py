# Prompt version: v2
# Used by: services/interview_graph.py
#
# v2 changes vs v1:
#   - build_question_prompt accepts an optional gap_category ("B" | "C" | None)
#   - Category B gaps produce confirmation questions ("You likely have X — can you describe it?")
#   - Category C gaps produce exploratory questions ("Tell me about your experience with X")

import json

# ---------------------------------------------------------------------------
# QuestionGenerator node
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
  "gap_addressed": true or false
}

Rules:
- Only include data EXPLICITLY stated in the answer — do not infer or fabricate
- gap_addressed: true if the answer provides meaningful, concrete information about the gap
- If the answer is vague, off-topic, or empty: return empty arrays and gap_addressed: false
- Omit work_history_to_add entries where both company and role are null"""


def build_response_parser_prompt(gap: str, question: str, answer: str) -> str:
    return (
        f"Gap being addressed: {gap}\n\n"
        f"Question asked: {question}\n\n"
        f"Candidate's answer: {answer}\n\n"
        "Extract the structured profile data."
    )
