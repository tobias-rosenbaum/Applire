"""Extract recipient name from a job description text.

Uses a regex cascade over common DACH and EN patterns.
Returns a dict with 'name' (str | None).
The LLM fallback is handled at generation time in services/cover_letter.py
if name is None and motivation/context warrants it.
"""

import re
from typing import TypedDict


class RecipientInfo(TypedDict):
    name: str | None


# Ordered from most-specific to least-specific
_PATTERNS: list[re.Pattern] = [
    # German: "richten Sie Ihre Bewerbung an <Title> <Name>"
    re.compile(
        r"richten\s+Sie\s+(?:Ihre\s+)?(?:Bewerbung|Unterlagen)\s+an\s+((?:Dr\.|Prof\.(?:\s+Dr\.)?|Dipl\.-\w+\.?)?\s*[A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)",
        re.UNICODE,
    ),
    # German: "an Frau/Herrn Dr./Prof. Vorname Nachname"
    re.compile(
        r"(?:an\s+)?(?:Frau|Herrn?)\s+((?:Dr\.|Prof\.(?:\s+Dr\.)?|Dipl\.-\w+\.?)\s+)?([A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?\s+[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?)",
        re.UNICODE,
    ),
    # English: "to Mr./Mrs./Ms./Dr. Firstname Lastname"
    re.compile(
        r"(?:to\s+)?(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?\s+[A-Z][a-z]+(?:-[A-Z][a-z]+)?)",
        re.UNICODE,
    ),
    # English: "contact <Name>, <role>"
    re.compile(
        r"contact\s+((?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+)?([A-Z][a-z]+\s+[A-Z][a-z]+)\s*,",
        re.UNICODE,
    ),
]


def extract_recipient_from_jd(raw_text: str) -> RecipientInfo:
    """Return {'name': str | None} extracted from the JD text."""
    for pattern in _PATTERNS:
        match = pattern.search(raw_text)
        if match:
            groups = [g for g in match.groups() if g]
            name = " ".join(groups).strip()
            # Collapse multiple spaces
            name = re.sub(r"\s+", " ", name)
            return RecipientInfo(name=name)
    return RecipientInfo(name=None)
