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

# Prompt version: v1
# Used by: services/skill_enrichment.py → enrich_skills() → LLMProvider.aparse_json
#
# Single batch call: estimates years_experience for skills not found in any
# WorkEntry.technologies list. Receives full work history for context.

import json

SKILL_ESTIMATION_SYSTEM_PROMPT = """\
You are a career analyst. Given a candidate's complete work history and a list of skill names,
estimate how many years of experience the candidate has with each skill based ONLY on the
provided work history.

Rules:
- Base all estimates exclusively on the provided work history — do not fabricate or infer beyond what is stated.
- If a skill is mentioned implicitly by a role's responsibilities or industry context but no specific
  duration can be determined from the dates, use null.
- If there is genuinely no basis for estimating a skill's duration, use null.
- Return integer years only — no fractions, no ranges.
- Do not include skills not present in the input list.

Respond ONLY with a valid JSON object — no markdown, no explanations:
{"SkillName": integer_or_null, ...}"""


def build_skill_estimation_prompt(
    work_experience: list[dict],
    skill_names: list[str],
) -> str:
    """Build the user message for the skill estimation LLM call.

    Args:
        work_experience: List of WorkEntry dicts (serialised via model_dump).
        skill_names:     Skills to estimate — only names, no other metadata.
    """
    work_history_json = json.dumps(work_experience, ensure_ascii=False, indent=2)
    skills_json = json.dumps(skill_names, ensure_ascii=False)
    return (
        f"Work history:\n{work_history_json}\n\n"
        f"Estimate years of experience for each of the following skills:\n{skills_json}\n\n"
        'Return a JSON object: {"SkillName": integer_or_null, ...}'
    )
