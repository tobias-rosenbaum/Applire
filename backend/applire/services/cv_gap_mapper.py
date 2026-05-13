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

"""Keyword-based gap-to-section mapper (no LLM, ~5ms).

For each gap label, tokenise it and count how many of its tokens appear
in each section's content. A gap is assigned to every section whose content
contains at least one matching token — the same gap can appear under multiple
sections if it is relevant to each. Gaps with zero matches in any section fall
into the __general__ bucket.
"""
import re


def _tokenise(text: str) -> set[str]:
    """Lowercase word tokens, 2+ chars."""
    return {w for w in re.findall(r"\b[a-zA-ZÀ-ÿ0-9.#+\-]{2,}\b", text.lower())}


def map_gaps_to_sections(
    gaps: list[str],
    sections: dict[str, str],  # section_id -> section content
) -> dict[str, list[str]]:
    """Return a dict mapping section_id -> [gap_labels] assigned to that section.

    Unmatched gaps are placed under the key "__general__".
    """
    if not gaps:
        return {}

    # Pre-tokenise section contents once
    section_tokens: dict[str, set[str]] = {
        sid: _tokenise(content) for sid, content in sections.items()
    }

    result: dict[str, list[str]] = {}

    for gap in gaps:
        gap_tokens = _tokenise(gap)
        if not gap_tokens:
            result.setdefault("__general__", []).append(gap)
            continue

        matched = False
        for sid, tokens in section_tokens.items():
            score = len(gap_tokens & tokens)
            if score > 0:
                result.setdefault(sid, []).append(gap)
                matched = True

        if not matched:
            result.setdefault("__general__", []).append(gap)

    return result
