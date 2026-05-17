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

"""Drift-guard tests for refinement-mode system prompts.

Each refinement prompt MUST:
- Exist as a module-level constant.
- Contain a distinctive lowercase fingerprint that the mock LLM can detect.
- Frame the task as "patch this JSON", not "extract from text".
- Be substantially shorter than its corresponding extraction prompt (target <=1.5 KB).
"""


def test_cv_extraction_refinement_prompt_exists_and_is_distinct():
    from applire.prompts.cv_extraction import (
        CV_EXTRACTION_REFINEMENT_PROMPT,
        GENERIC_CV_EXTRACTION_PROMPT,
    )

    assert isinstance(CV_EXTRACTION_REFINEMENT_PROMPT, str)
    assert "cv profile corrector" in CV_EXTRACTION_REFINEMENT_PROMPT.lower()
    assert "patch" in CV_EXTRACTION_REFINEMENT_PROMPT.lower()
    assert len(CV_EXTRACTION_REFINEMENT_PROMPT) < len(GENERIC_CV_EXTRACTION_PROMPT)
    assert len(CV_EXTRACTION_REFINEMENT_PROMPT) <= 1500


def test_profile_extraction_refinement_prompt_exists_and_is_distinct():
    from applire.prompts.profile_extraction import (
        PROFILE_EXTRACTION_REFINEMENT_PROMPT,
        SYSTEM_PROMPT,
    )

    assert isinstance(PROFILE_EXTRACTION_REFINEMENT_PROMPT, str)
    assert "profile data corrector" in PROFILE_EXTRACTION_REFINEMENT_PROMPT.lower()
    assert "patch" in PROFILE_EXTRACTION_REFINEMENT_PROMPT.lower()
    assert len(PROFILE_EXTRACTION_REFINEMENT_PROMPT) < len(SYSTEM_PROMPT)
    assert len(PROFILE_EXTRACTION_REFINEMENT_PROMPT) <= 1500


def test_cv_tailoring_refinement_prompt_exists_and_is_distinct():
    from applire.prompts.cv_tailoring import (
        CV_TAILORING_REFINEMENT_PROMPT,
        SYSTEM_PROMPT,
    )

    assert isinstance(CV_TAILORING_REFINEMENT_PROMPT, str)
    assert "tailored cv corrector" in CV_TAILORING_REFINEMENT_PROMPT.lower()
    assert "patch" in CV_TAILORING_REFINEMENT_PROMPT.lower()
    assert len(CV_TAILORING_REFINEMENT_PROMPT) < len(SYSTEM_PROMPT)
    assert len(CV_TAILORING_REFINEMENT_PROMPT) <= 1500


def test_response_parser_refinement_prompt_exists_and_is_distinct():
    from applire.prompts.review_interview_response import (
        RESPONSE_PARSER_REFINEMENT_PROMPT,
    )

    assert isinstance(RESPONSE_PARSER_REFINEMENT_PROMPT, str)
    assert "answer parser corrector" in RESPONSE_PARSER_REFINEMENT_PROMPT.lower()
    assert "patch" in RESPONSE_PARSER_REFINEMENT_PROMPT.lower()
    assert len(RESPONSE_PARSER_REFINEMENT_PROMPT) <= 1500
    assert len(RESPONSE_PARSER_REFINEMENT_PROMPT) >= 100  # non-trivial
