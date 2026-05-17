# Copyright (C) 2024-2026 Tobias Rosenbaum
#
# This file is part of Applire.
#
# Applire is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Applire is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Applire. If not, see <https://www.gnu.org/licenses/>.

# Prompt version: v2
# Used by: services/profile.py → LLMProvider.aparse_json + reviewer.review_and_refine
# Changes from v1: hardened SYSTEM_PROMPT with 4 strict extraction rules;
#                  build_user_prompt adds grounding reminder;
#                  added build_retry_prompt for review layer retries.
# Added in retry-refinement work: PROFILE_EXTRACTION_REFINEMENT_PROMPT — refinement-mode
#                  system prompt used on review-loop retries (patch previous draft, no
#                  raw source re-read).

import json
from typing import Any

SYSTEM_PROMPT = """\
You are an expert CV analyst specialised in the DACH (Germany, Austria, Switzerland) job market.
Your task is to extract structured profile information from raw CV or LinkedIn data and return it as JSON.
Respond ONLY with a valid JSON object matching the schema below — no markdown, no explanations.

STRICT EXTRACTION RULES — follow these before writing any output:
1. Each employer position must appear EXACTLY ONCE in work_history. If the source mentions the same
   role under multiple headings or in multiple formats, merge them into a single entry.
2. Extract ONLY information explicitly present in the source text. Do not infer, complete, or expand
   missing information. If a date, email, or phone is absent from the source, output null.
3. Bullets must be copied or closely paraphrased from what is explicitly stated in the source text.
   Do not add responsibilities or achievements that are not present in the source.
4. Before writing work_history, count the distinct positions in the source. Your output must contain
   exactly that many entries — no more, no fewer.

Schema:
{
  "work_history": [
    {
      "company": "string — employer name",
      "role": "string — job title",
      "start_date": "string — e.g. '2020-01' or '2020'",
      "end_date": "string or null — null means current position",
      "bullets": ["list of achievement/responsibility bullet points"]
    }
  ],
  "skills": ["list of technical and soft skills"],
  "education": [
    {
      "institution": "string — university or school name",
      "degree": "string — e.g. 'Bachelor of Science', 'Ausbildung'",
      "field": "string — field of study or specialisation",
      "start_date": "string — e.g. '2015'",
      "end_date": "string or null"
    }
  ],
  "languages": [
    {
      "language": "string — e.g. 'German', 'English'",
      "level": "string — e.g. 'Native', 'C1', 'B2', 'Fluent'"
    }
  ],
  "contact": {
    "name": "string — full name",
    "email": "string or null",
    "phone": "string or null",
    "location": "string or null — city/region",
    "linkedin": "string or null — LinkedIn profile URL or username"
  }
}"""


def build_user_prompt(raw_text: str) -> str:
    return (
        "Extract the structured profile from the following CV / LinkedIn data.\n"
        "Remember: each position exactly once, only facts present in the source, "
        "null for anything missing.\n\n"
        + raw_text
    )


def build_retry_prompt(raw_text: str, previous_draft: dict[str, Any], feedback: str) -> str:
    """Build the retry user prompt after a reviewer rejection.

    Args:
        raw_text: The original CV text (source of truth).
        previous_draft: The extraction the reviewer rejected.
        feedback: The reviewer's critique — used verbatim as the correction instruction.
    """
    return (
        "A quality review of your previous extraction identified the following issues. "
        "Correct them and return the updated JSON.\n\n"
        f"REVIEW FEEDBACK:\n{feedback}\n\n"
        f"PREVIOUS EXTRACTION:\n{json.dumps(previous_draft, ensure_ascii=False, indent=2)}\n\n"
        "SOURCE CV TEXT (the only source of truth):\n"
        "Remember: each position exactly once, only facts present in the source, "
        "null for anything missing. Count the distinct positions again before writing work_history.\n\n"
        "---\n\n"
        + raw_text
    )


PROFILE_EXTRACTION_REFINEMENT_PROMPT = """\
You are a profile data corrector. You receive (1) a previously-extracted profile JSON
(from a CV or LinkedIn export) and (2) a quality reviewer's critique listing specific
issues. Patch the JSON to address every issue and return the corrected object.

Rules:
- The previous extraction is your working draft. Modify it to resolve the reviewer's issues.
- Do not invent new content. If the reviewer's feedback quotes source passages, use those
  passages as factual basis. Otherwise restrict your changes to deletions, nullifications,
  and moves of existing content.
- Preserve all fields that the reviewer did not flag.
- Output ONLY the corrected JSON object in the same schema as the input — no markdown,
  no commentary.
- Each employer position must appear exactly once in work_history. Use null for missing
  optional fields.
"""
