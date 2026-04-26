# Prompt version: v1
# Used by: services/profile/__init__.py → upload_cv() → reviewer.review_and_refine
#
# Mirrors review_profile_extraction.py but uses work_experience field names
# (responsibilities, achievements, technologies) instead of work_history/bullets.
# A separate file is required because the LinkedIn reviewer references "work_history"
# in its rules — wiring it to the CV upload path would cause false rejections.

import json
from typing import Any

CV_EXTRACTION_REVIEW_SYSTEM_PROMPT = """\
You are a strict CV data quality auditor. Your task is to verify that an extracted
profile JSON faithfully represents the source CV text — nothing more, nothing less.

Check for ALL of the following:
1. DUPLICATE ENTRIES: Each employer and role must appear exactly once in work_experience.
   Flag any entry that is a duplicate or variant of another entry (same company/role,
   different or missing dates).
2. FABRICATED ENTRIES: Every work_experience entry must have a clear corresponding passage
   in the source text. Flag any entry with no basis in the source.
3. INVENTED DATES: start_date and end_date must match exactly what is stated in the source.
   If a date is absent from the source, the field must be null — never inferred or invented.
4. INVENTED CONTENT: responsibilities, achievements, and technologies must reflect what is
   explicitly stated in the source text. Flag any item that adds content not present in the source.
5. EMPTY/SHELL ENTRIES: Flag any work_experience entry with an empty or null company name ("").
   These are invalid — the role should either be removed or placed as a role_alias on an existing entry.
6. MISPLACED ROLE ALIASES: Flag any work_experience entry that has a company name but is missing
   BOTH start_date AND responsibilities/achievements. These are almost certainly role titles mentioned
   within another position and should appear in that position's role_aliases list, not as a separate entry.

Respond ONLY with a valid JSON object — no markdown, no explanations:
{
  "approved": true or false,
  "issues": ["list of specific issues with work_experience index and description — empty array if approved"],
  "feedback": "concise instruction for the extractor to correct all issues — empty string if approved"
}"""


def build_cv_extraction_review_prompt(raw_cv_text: str, extracted_json: dict) -> str:
    """Build the reviewer user prompt for CV extraction.

    Args:
        raw_cv_text:    The original CV text the profile was extracted from.
        extracted_json: The profile JSON produced by the extraction agent.
    """
    return (
        "Review this extracted profile against the source CV text.\n\n"
        f"SOURCE CV TEXT:\n{raw_cv_text}\n\n"
        f"EXTRACTED PROFILE:\n{json.dumps(extracted_json, ensure_ascii=False, indent=2)}\n\n"
        "Does the extracted profile faithfully and completely represent the source — "
        "no duplicates, no fabrications, no invented dates, no invented content? "
        "Return your review JSON."
    )


def build_cv_extraction_retry_prompt(
    raw_cv_text: str,
    previous_draft: dict[str, Any],
    feedback: str,
) -> str:
    """Build the retry user prompt after a reviewer rejection of a CV extraction.

    Args:
        raw_cv_text:    The original CV text (source of truth).
        previous_draft: The extraction the reviewer rejected.
        feedback:       The reviewer's critique — used verbatim as the correction instruction.
    """
    return (
        "A quality review of your previous extraction identified the following issues. "
        "Correct them and return the updated JSON.\n\n"
        f"REVIEW FEEDBACK:\n{feedback}\n\n"
        f"PREVIOUS EXTRACTION:\n{json.dumps(previous_draft, ensure_ascii=False, indent=2)}\n\n"
        "SOURCE CV TEXT (the only source of truth):\n"
        "Remember: each position exactly once, only facts present in the source, "
        "null for anything missing. Count the distinct positions again before writing work_experience.\n\n"
        "---\n\n"
        + raw_cv_text
    )
