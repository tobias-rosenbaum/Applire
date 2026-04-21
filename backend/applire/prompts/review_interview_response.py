# Prompt version: v1
# Used by: services/interview_graph.py → ResponseParser node (Mode C)
#          wrapped with reviewer.review_and_refine

import json

RESPONSE_PARSER_REVIEW_SYSTEM_PROMPT = """\
You are a quality reviewer for structured profile data extracted from a conversational answer.
Your job is to verify that extracted data faithfully represents what the user actually said.
You must not approve data that was hallucinated or inferred beyond what was stated.
Respond with JSON only: {"approved": bool, "issues": list[str], "feedback": str}
- approved: true only if all extracted fields are accurate and grounded in the answer
- issues: list of specific problems found (empty list if approved)
- feedback: one concise sentence telling the generator how to fix the draft (empty string if approved)
"""


def build_response_parser_review_prompt(
    gap: str,
    question: str,
    answer: str,
    draft: dict,
) -> str:
    return f"""\
Review the following extracted profile data.

Gap being addressed: {gap}
Question asked: {question}
User's answer: {answer}

Extracted draft:
{json.dumps(draft, indent=2, ensure_ascii=False)}

Check all of the following:
1. Are extracted achievements specific and concrete — not paraphrased into vague generalities?
2. Do numeric values (team_size, budget_managed) exactly match what the user stated?
3. Is every field in the draft actually grounded in the user's answer — no hallucination?
4. If the user said they had no budget responsibility, is budget_managed absent or null (not fabricated)?

Respond with JSON only:
{{"approved": bool, "issues": list[str], "feedback": str}}
"""
