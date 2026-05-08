# LLM Review Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reviewer-guided retry loop to the profile extraction and CV tailoring LLM steps to catch and correct hallucinations before they are persisted.

**Architecture:** A generic `review_and_refine()` function in `services/reviewer.py` runs a reviewer LLM call after each generator LLM call. If the reviewer rejects the draft it feeds a critique back to the generator and retries. Both generator prompts are hardened with explicit grounding rules to reduce hallucination probability before the reviewer even runs.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Mistral AI via existing `LLMProvider` abstraction, pytest + AsyncMock for tests.

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| **Create** | `backend/applire/services/reviewer.py` | Generic `review_and_refine()` retry loop |
| **Create** | `backend/applire/prompts/review_profile_extraction.py` | Reviewer prompts for profile extraction |
| **Create** | `backend/applire/prompts/review_cv_tailoring.py` | Reviewer prompts for CV tailoring |
| **Create** | `tests/unit/test_reviewer.py` | Unit tests for retry loop behaviour |
| **Create** | `tests/unit/test_review_prompts.py` | Smoke tests for prompt rendering |
| **Modify** | `backend/applire/constants.py` | Add `LLM_REVIEW_MAX_RETRIES` |
| **Modify** | `backend/applire/prompts/profile_extraction.py` | Harden to v2, add `build_retry_prompt` |
| **Modify** | `backend/applire/prompts/cv_tailoring.py` | Harden to v2, add `build_retry_prompt` |
| **Modify** | `backend/applire/services/profile.py` | Call `review_and_refine` after extraction |
| **Modify** | `backend/applire/services/cv.py` | Call `review_and_refine` after tailoring |
| **Modify** | `docker-compose.yml` | Document `LLM_REVIEW_MAX_RETRIES` env var |

---

## Task 1: Add `LLM_REVIEW_MAX_RETRIES` to constants

**Files:**
- Modify: `backend/applire/constants.py`

- [ ] **Step 1: Add the constant**

Open `backend/applire/constants.py` and append:

```python
# LLM review layer — retry ceiling (ADR-021, Sprint 20)
# Set LLM_REVIEW_MAX_RETRIES=0 to disable the review layer entirely.
LLM_REVIEW_MAX_RETRIES: int = int(
    os.environ.get("LLM_REVIEW_MAX_RETRIES", "2")
)
```

- [ ] **Step 2: Verify it imports cleanly**

```bash
cd /home/apliqa/Documents/Applire/Solution
python -c "from applire.constants import LLM_REVIEW_MAX_RETRIES; print(LLM_REVIEW_MAX_RETRIES)"
```

Expected output: `2`

- [ ] **Step 3: Commit**

```bash
git add backend/applire/constants.py
git commit -m "feat(review): add LLM_REVIEW_MAX_RETRIES constant (ADR-021)"
```

---

## Task 2: Create `services/reviewer.py` (TDD)

**Files:**
- Create: `tests/unit/test_reviewer.py`
- Create: `backend/applire/services/reviewer.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_reviewer.py`:

```python
"""
Unit tests for services/reviewer.py — review_and_refine() retry loop.

No Docker, no DB, no real LLM.

Run:
    pytest tests/unit/test_reviewer.py -v
"""
import sys
import logging
from pathlib import Path
from unittest.mock import AsyncMock, call

import pytest

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from applire.services.reviewer import review_and_refine


@pytest.fixture
def mock_provider():
    provider = AsyncMock()
    return provider


# ---------------------------------------------------------------------------
# max_retries=0 — disabled path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_max_retries_zero_returns_draft_immediately(mock_provider):
    """When max_retries=0 the review layer is disabled — no LLM calls at all."""
    draft = {"work_history": [{"company": "Acme"}]}
    result = await review_and_refine(
        source="Acme Software Developer 2020-2022",
        draft=draft,
        generator_prompt_fn=lambda s, d, f: "retry prompt",
        generator_system="gen system",
        reviewer_prompt_fn=lambda s, d: "review prompt",
        reviewer_system="rev system",
        provider=mock_provider,
        max_retries=0,
    )
    assert result is draft
    mock_provider.aparse_json.assert_not_called()


# ---------------------------------------------------------------------------
# Approves on first reviewer call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approves_on_first_pass_returns_draft_unchanged(mock_provider):
    """If reviewer approves immediately, draft is returned as-is."""
    draft = {"work_history": [{"company": "Acme", "role": "Dev"}]}
    mock_provider.aparse_json.return_value = {
        "approved": True,
        "issues": [],
        "feedback": "",
    }

    result = await review_and_refine(
        source="Acme Dev 2020-2022",
        draft=draft,
        generator_prompt_fn=lambda s, d, f: f"retry: {f}",
        generator_system="gen system",
        reviewer_prompt_fn=lambda s, d: "review prompt",
        reviewer_system="rev system",
        provider=mock_provider,
        max_retries=2,
    )

    assert result == draft
    # Only the reviewer is called — no generator retry
    assert mock_provider.aparse_json.call_count == 1


# ---------------------------------------------------------------------------
# Rejects once, then approves
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rejects_once_then_approves_returns_revised_draft(mock_provider):
    """One rejection triggers one generator retry; second review approves."""
    original = {"work_history": [{"company": "Acme", "role": "Dev"}]}
    revised = {"work_history": [{"company": "Acme", "role": "Dev", "start_date": "2020"}]}

    mock_provider.aparse_json.side_effect = [
        # Reviewer call 1: reject
        {"approved": False, "issues": ["start_date missing"], "feedback": "Add start_date from source"},
        # Generator retry 1: revised draft
        revised,
        # Reviewer call 2: approve
        {"approved": True, "issues": [], "feedback": ""},
    ]

    result = await review_and_refine(
        source="Acme Dev 2020-2022",
        draft=original,
        generator_prompt_fn=lambda s, d, f: f"retry with feedback: {f}",
        generator_system="gen system",
        reviewer_prompt_fn=lambda s, d: "review prompt",
        reviewer_system="rev system",
        provider=mock_provider,
        max_retries=2,
    )

    assert result == revised
    assert mock_provider.aparse_json.call_count == 3


# ---------------------------------------------------------------------------
# Retry exhaustion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exhausts_retries_returns_last_draft_and_logs_warning(mock_provider, caplog):
    """When all retries are exhausted, the last generated draft is returned and a warning logged."""
    original = {"work_history": [{"company": "Bad Co"}]}
    retry1 = {"work_history": [{"company": "Still Bad Co"}]}
    retry2 = {"work_history": [{"company": "Final Co"}]}

    mock_provider.aparse_json.side_effect = [
        # attempt 0: reviewer rejects
        {"approved": False, "issues": ["fabricated entry"], "feedback": "Remove fabricated entry"},
        # attempt 0: generator retry
        retry1,
        # attempt 1: reviewer rejects again
        {"approved": False, "issues": ["still fabricated"], "feedback": "Try harder"},
        # attempt 1: generator retry
        retry2,
    ]

    with caplog.at_level(logging.WARNING, logger="applire.services.reviewer"):
        result = await review_and_refine(
            source="original cv text",
            draft=original,
            generator_prompt_fn=lambda s, d, f: f"retry: {f}",
            generator_system="gen system",
            reviewer_prompt_fn=lambda s, d: "review prompt",
            reviewer_system="rev system",
            provider=mock_provider,
            max_retries=2,
        )

    assert result == retry2
    assert mock_provider.aparse_json.call_count == 4
    assert "exhausted" in caplog.text


# ---------------------------------------------------------------------------
# Reviewer prompt is called with correct arguments
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reviewer_receives_source_and_current_draft(mock_provider):
    """Verifies the reviewer is called with (source, current_draft)."""
    draft = {"key": "value"}
    received_args: list[tuple] = []

    def capture_reviewer(source: str, d: dict) -> str:
        received_args.append((source, d))
        return "review prompt"

    mock_provider.aparse_json.return_value = {"approved": True, "issues": [], "feedback": ""}

    await review_and_refine(
        source="the source material",
        draft=draft,
        generator_prompt_fn=lambda s, d, f: "retry",
        generator_system="gen",
        reviewer_prompt_fn=capture_reviewer,
        reviewer_system="rev",
        provider=mock_provider,
        max_retries=1,
    )

    assert received_args == [("the source material", draft)]


# ---------------------------------------------------------------------------
# Generator retry receives feedback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generator_retry_receives_feedback_string(mock_provider):
    """Verifies the generator retry is called with the reviewer's feedback."""
    draft = {"key": "original"}
    received_args: list[tuple] = []

    def capture_generator(source: str, d: dict, feedback: str) -> str:
        received_args.append((source, d, feedback))
        return "retry prompt"

    mock_provider.aparse_json.side_effect = [
        {"approved": False, "issues": ["x"], "feedback": "specific critique"},
        {"key": "revised"},
        {"approved": True, "issues": [], "feedback": ""},
    ]

    await review_and_refine(
        source="the source",
        draft=draft,
        generator_prompt_fn=capture_generator,
        generator_system="gen",
        reviewer_prompt_fn=lambda s, d: "review prompt",
        reviewer_system="rev",
        provider=mock_provider,
        max_retries=2,
    )

    assert received_args[0] == ("the source", draft, "specific critique")
```

- [ ] **Step 2: Run tests to confirm they all fail**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_reviewer.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'applire.services.reviewer'`

- [ ] **Step 3: Create `backend/applire/services/reviewer.py`**

```python
"""LLM Review Layer — reviewer-guided retry loop (ADR-021, Sprint 20).

review_and_refine() runs a reviewer LLM call after the initial generator output.
If the reviewer rejects the draft it feeds the critique back to the generator
and retries, up to max_retries times.

Never raises — on retry exhaustion the last draft is returned and a WARNING
is logged so the issue is observable without breaking the caller's flow.
"""

import logging
from collections.abc import Callable
from typing import Any

from applire.providers.llm.base import LLMProvider

logger = logging.getLogger(__name__)


async def review_and_refine(
    source: str,
    draft: dict[str, Any],
    generator_prompt_fn: Callable[[str, dict, str], str],
    generator_system: str,
    reviewer_prompt_fn: Callable[[str, dict], str],
    reviewer_system: str,
    provider: LLMProvider,
    max_retries: int,
) -> dict[str, Any]:
    """Run a reviewer-guided retry loop over an LLM generator output.

    Args:
        source: The original source material the reviewer checks the draft against
                (raw CV text for extraction; serialised profile JSON for tailoring).
        draft: The initial generator output to be reviewed.
        generator_prompt_fn: Called as fn(source, previous_draft, feedback) → prompt str.
                             Used to build the retry user prompt.
        generator_system: The generator's system prompt (unchanged across retries).
        reviewer_prompt_fn: Called as fn(source, draft) → prompt str.
        reviewer_system: The reviewer's system prompt.
        provider: LLM provider — same instance used by the calling service.
        max_retries: Maximum number of generator retries. 0 = review layer disabled.

    Returns:
        The approved draft, or the last generated draft if retries are exhausted.
    """
    if max_retries == 0:
        return draft

    current_draft = draft
    last_issues: list[str] = []

    for attempt in range(max_retries):
        review: dict = await provider.aparse_json(
            reviewer_prompt_fn(source, current_draft),
            system=reviewer_system,
            temperature=0.1,
        )

        if review.get("approved", False):
            return current_draft

        last_issues = review.get("issues", [])
        feedback = review.get("feedback", "")
        logger.debug(
            "review_and_refine attempt %d/%d rejected. Issues: %r",
            attempt + 1,
            max_retries,
            last_issues,
        )

        current_draft = await provider.aparse_json(
            generator_prompt_fn(source, current_draft, feedback),
            system=generator_system,
            temperature=0.1,
        )

    logger.warning(
        "review_and_refine: %d retries exhausted. Last known issues: %r",
        max_retries,
        last_issues,
    )
    return current_draft
```

- [ ] **Step 4: Run tests — all must pass**

```bash
pytest tests/unit/test_reviewer.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/reviewer.py tests/unit/test_reviewer.py
git commit -m "feat(review): add review_and_refine() retry loop service (ADR-021)"
```

---

## Task 3: Create reviewer prompts for profile extraction

**Files:**
- Create: `backend/applire/prompts/review_profile_extraction.py`
- Create: `tests/unit/test_review_prompts.py` (partial — extended in Task 6)

- [ ] **Step 1: Write the failing smoke test**

Create `tests/unit/test_review_prompts.py`:

```python
"""
Smoke tests for review prompt builders — verify they render without error.

No LLM calls. No Docker.

Run:
    pytest tests/unit/test_review_prompts.py -v
"""
import sys
from pathlib import Path

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


_SAMPLE_PROFILE = {
    "work_history": [
        {
            "company": "Acme GmbH",
            "role": "Software Developer",
            "start_date": "2020-01",
            "end_date": "2022-12",
            "bullets": ["Built APIs", "Led migrations"],
        }
    ],
    "skills": ["Python", "FastAPI"],
    "education": [],
    "languages": [{"language": "German", "level": "Native"}],
    "contact": {"name": "Max Muster", "email": None, "phone": None, "location": "Berlin", "linkedin": None},
}

_SAMPLE_RAW_CV = "Acme GmbH — Software Developer (Jan 2020 – Dec 2022)\n- Built APIs\n- Led migrations"


class TestProfileExtractionReviewPrompts:
    def test_build_review_prompt_returns_nonempty_string(self):
        from applire.prompts.review_profile_extraction import build_review_prompt

        result = build_review_prompt(_SAMPLE_RAW_CV, _SAMPLE_PROFILE)
        assert isinstance(result, str)
        assert len(result) > 50

    def test_build_review_prompt_includes_source_text(self):
        from applire.prompts.review_profile_extraction import build_review_prompt

        result = build_review_prompt(_SAMPLE_RAW_CV, _SAMPLE_PROFILE)
        assert "Acme GmbH" in result

    def test_build_review_prompt_includes_extracted_json(self):
        from applire.prompts.review_profile_extraction import build_review_prompt

        result = build_review_prompt(_SAMPLE_RAW_CV, _SAMPLE_PROFILE)
        assert "Software Developer" in result

    def test_review_system_prompt_is_nonempty_string(self):
        from applire.prompts.review_profile_extraction import REVIEW_SYSTEM_PROMPT

        assert isinstance(REVIEW_SYSTEM_PROMPT, str)
        assert len(REVIEW_SYSTEM_PROMPT) > 100
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
pytest tests/unit/test_review_prompts.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'applire.prompts.review_profile_extraction'`

- [ ] **Step 3: Create `backend/applire/prompts/review_profile_extraction.py`**

```python
# Prompt version: v1
# Used by: services/profile.py → reviewer.review_and_refine

import json

REVIEW_SYSTEM_PROMPT = """\
You are a strict CV data quality auditor. Your task is to verify that an extracted
profile JSON faithfully represents the source CV text — nothing more, nothing less.

Check for ALL of the following:
1. DUPLICATE ENTRIES: Each employer and role must appear exactly once in work_history.
   Flag any entry that is a duplicate or variant of another entry (same company/role,
   different or missing dates).
2. FABRICATED ENTRIES: Every work_history entry must have a clear corresponding passage
   in the source text. Flag any entry with no basis in the source.
3. INVENTED DATES: start_date and end_date must match exactly what is stated in the source.
   If a date is absent from the source, the field must be null — never inferred or invented.
4. INVENTED BULLETS: Bullets must reflect what is explicitly stated in the source text.
   Flag any bullet that adds responsibilities, achievements, or skills not present in the source.

Respond ONLY with a valid JSON object — no markdown, no explanations:
{
  "approved": true or false,
  "issues": ["list of specific issues with work_history index and description — empty array if approved"],
  "feedback": "concise instruction for the extractor to correct all issues — empty string if approved"
}"""


def build_review_prompt(raw_cv_text: str, extracted_json: dict) -> str:
    """Build the reviewer user prompt for profile extraction.

    Args:
        raw_cv_text: The original CV text the profile was extracted from.
        extracted_json: The profile JSON produced by the extraction agent.
    """
    return (
        "Review this extracted profile against the source CV text.\n\n"
        f"SOURCE CV TEXT:\n{raw_cv_text}\n\n"
        f"EXTRACTED PROFILE:\n{json.dumps(extracted_json, ensure_ascii=False, indent=2)}\n\n"
        "Does the extracted profile faithfully and completely represent the source — "
        "no duplicates, no fabrications, no invented dates? Return your review JSON."
    )
```

- [ ] **Step 4: Run smoke tests — all must pass**

```bash
pytest tests/unit/test_review_prompts.py::TestProfileExtractionReviewPrompts -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/applire/prompts/review_profile_extraction.py tests/unit/test_review_prompts.py
git commit -m "feat(review): add profile extraction reviewer prompt (ADR-021)"
```

---

## Task 4: Harden `prompts/profile_extraction.py` to v2

**Files:**
- Modify: `backend/applire/prompts/profile_extraction.py`

- [ ] **Step 1: Add smoke tests for the new functions**

Append to `tests/unit/test_review_prompts.py`:

```python
class TestProfileExtractionGeneratorPrompts:
    def test_build_user_prompt_includes_raw_text(self):
        from applire.prompts.profile_extraction import build_user_prompt

        result = build_user_prompt("Max Muster — Acme GmbH")
        assert "Max Muster" in result
        assert "exactly once" in result  # grounding reminder

    def test_build_retry_prompt_includes_feedback(self):
        from applire.prompts.profile_extraction import build_retry_prompt

        result = build_retry_prompt(
            raw_text="Acme GmbH 2020-2022",
            previous_draft={"work_history": []},
            feedback="Remove duplicate at index 1",
        )
        assert "Remove duplicate at index 1" in result
        assert "Acme GmbH 2020-2022" in result

    def test_build_retry_prompt_includes_previous_draft(self):
        from applire.prompts.profile_extraction import build_retry_prompt

        previous = {"work_history": [{"company": "Acme"}]}
        result = build_retry_prompt(
            raw_text="source",
            previous_draft=previous,
            feedback="fix it",
        )
        assert "Acme" in result
```

- [ ] **Step 2: Run to confirm new tests fail**

```bash
pytest tests/unit/test_review_prompts.py::TestProfileExtractionGeneratorPrompts -v
```

Expected: `FAILED` — `build_retry_prompt` not yet defined, `build_user_prompt` missing grounding reminder.

- [ ] **Step 3: Replace `backend/applire/prompts/profile_extraction.py`**

```python
# Prompt version: v2
# Used by: services/profile.py → LLMProvider.aparse_json + reviewer.review_and_refine
# Changes from v1: hardened SYSTEM_PROMPT with 4 strict extraction rules;
#                  build_user_prompt adds grounding reminder;
#                  added build_retry_prompt for review layer retries.

import json

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


def build_retry_prompt(raw_text: str, previous_draft: dict, feedback: str) -> str:
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
        "null for anything missing.\n\n"
        + raw_text
    )
```

- [ ] **Step 4: Run all prompt tests**

```bash
pytest tests/unit/test_review_prompts.py -v
```

Expected: all existing tests + 3 new tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/prompts/profile_extraction.py tests/unit/test_review_prompts.py
git commit -m "feat(review): harden profile_extraction prompt to v2, add build_retry_prompt"
```

---

## Task 5: Integrate review into `services/profile.py`

**Files:**
- Modify: `backend/applire/services/profile.py`

- [ ] **Step 1: Write the integration test**

Append to `tests/unit/test_review_prompts.py`:

```python
class TestProfileServiceReviewIntegration:
    """Verify that _import_from_text calls review_and_refine with the right arguments."""

    @pytest.mark.asyncio
    async def test_import_from_text_passes_source_to_reviewer(self):
        import pytest
        from unittest.mock import AsyncMock, patch, MagicMock
        from applire.services.profile import _import_from_text

        extracted = {
            "work_history": [{"company": "Acme", "role": "Dev", "start_date": "2020", "end_date": None, "bullets": []}],
            "skills": [],
            "education": [],
            "languages": [],
            "contact": {"name": "Max", "email": None, "phone": None, "location": None, "linkedin": None},
        }

        mock_provider = AsyncMock()
        mock_provider.aparse_json.return_value = extracted

        # Patch review_and_refine to capture its arguments and pass the draft through
        captured: dict = {}

        async def fake_review(**kwargs):
            captured.update(kwargs)
            return kwargs["draft"]

        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with patch("applire.services.profile.review_and_refine", side_effect=fake_review):
            with patch("applire.services.profile.LLM_REVIEW_MAX_RETRIES", 2):
                await _import_from_text("Acme Dev 2020-2022", mock_db, mock_provider)

        assert captured.get("source") == "Acme Dev 2020-2022"
        assert captured.get("draft") == extracted
        assert captured.get("max_retries") == 2
```

Add the missing pytest import at the top of `test_review_prompts.py`:
```python
import pytest
```

- [ ] **Step 2: Run to confirm the test fails**

```bash
pytest tests/unit/test_review_prompts.py::TestProfileServiceReviewIntegration -v
```

Expected: `FAILED` — `review_and_refine` not yet imported in `profile.py`.

- [ ] **Step 3: Update `backend/applire/services/profile.py`**

Add these imports at the top (after existing imports):

```python
from applire.constants import LLM_REVIEW_MAX_RETRIES
from applire.prompts.profile_extraction import build_retry_prompt as _build_extraction_retry_prompt
from applire.prompts.review_profile_extraction import (
    REVIEW_SYSTEM_PROMPT as _EXTRACTION_REVIEW_SYSTEM_PROMPT,
    build_review_prompt as _build_extraction_review_prompt,
)
from applire.services.reviewer import review_and_refine
```

Replace `_import_from_text` with:

```python
async def _import_from_text(
    raw_text: str,
    db: AsyncSession,
    provider: LLMProvider,
) -> MasterProfileResponse:
    data: dict = await provider.aparse_json(
        build_user_prompt(raw_text),
        system=SYSTEM_PROMPT,
        temperature=0.1,
    )
    data = await review_and_refine(
        source=raw_text,
        draft=data,
        generator_prompt_fn=_build_extraction_retry_prompt,
        generator_system=SYSTEM_PROMPT,
        reviewer_prompt_fn=_build_extraction_review_prompt,
        reviewer_system=_EXTRACTION_REVIEW_SYSTEM_PROMPT,
        provider=provider,
        max_retries=LLM_REVIEW_MAX_RETRIES,
    )
    profile_data = _build_profile_data(data)
    profile_json = profile_data.model_dump()

    existing = await _get_latest(db)
    if existing:
        existing.profile_json = profile_json
        existing.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(existing)
        return _to_response(existing)

    record = MasterProfile(profile_json=profile_json)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _to_response(record)
```

- [ ] **Step 4: Run all unit tests**

```bash
pytest tests/unit/ -v
```

Expected: all tests pass (no regressions).

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/profile.py tests/unit/test_review_prompts.py
git commit -m "feat(review): integrate review_and_refine into profile extraction service"
```

---

## Task 6: Create reviewer prompts for CV tailoring

**Files:**
- Create: `backend/applire/prompts/review_cv_tailoring.py`
- Modify: `tests/unit/test_review_prompts.py`

- [ ] **Step 1: Write the failing smoke tests**

Append to `tests/unit/test_review_prompts.py`:

```python
_SAMPLE_TAILORED_CV = {
    "contact": {"name": "Max Muster", "email": None, "phone": None, "location": "Berlin", "linkedin": None},
    "summary": "Experienced developer targeting backend roles.",
    "work_history": [
        {
            "company": "Acme GmbH",
            "role": "Software Developer",
            "start_date": "2020-01",
            "end_date": "2022-12",
            "bullets": ["Built REST APIs with FastAPI"],
        }
    ],
    "skills": ["Python", "FastAPI"],
    "education": [],
    "languages": [{"language": "German", "level": "Native"}],
}

_SAMPLE_SOURCE_MATERIAL = '{"work_history": [{"company": "Acme GmbH", "role": "Software Developer"}]}'


class TestCVTailoringReviewPrompts:
    def test_build_review_prompt_returns_nonempty_string(self):
        from applire.prompts.review_cv_tailoring import build_review_prompt

        result = build_review_prompt(_SAMPLE_SOURCE_MATERIAL, _SAMPLE_TAILORED_CV)
        assert isinstance(result, str)
        assert len(result) > 50

    def test_build_review_prompt_includes_source_material(self):
        from applire.prompts.review_cv_tailoring import build_review_prompt

        result = build_review_prompt(_SAMPLE_SOURCE_MATERIAL, _SAMPLE_TAILORED_CV)
        assert "Acme GmbH" in result

    def test_build_review_prompt_includes_tailored_cv(self):
        from applire.prompts.review_cv_tailoring import build_review_prompt

        result = build_review_prompt(_SAMPLE_SOURCE_MATERIAL, _SAMPLE_TAILORED_CV)
        assert "FastAPI" in result

    def test_review_system_prompt_is_nonempty_string(self):
        from applire.prompts.review_cv_tailoring import REVIEW_SYSTEM_PROMPT

        assert isinstance(REVIEW_SYSTEM_PROMPT, str)
        assert len(REVIEW_SYSTEM_PROMPT) > 100
```

- [ ] **Step 2: Run to confirm tests fail**

```bash
pytest tests/unit/test_review_prompts.py::TestCVTailoringReviewPrompts -v
```

Expected: `ModuleNotFoundError: No module named 'applire.prompts.review_cv_tailoring'`

- [ ] **Step 3: Create `backend/applire/prompts/review_cv_tailoring.py`**

```python
# Prompt version: v1
# Used by: services/cv.py → reviewer.review_and_refine

import json

REVIEW_SYSTEM_PROMPT = """\
You are a strict CV quality auditor. Your task is to verify that a tailored CV JSON
contains only claims that are grounded in the candidate's master profile.

Check for ALL of the following:
1. FABRICATED BULLETS: Every bullet in work_history must be grounded in the CANDIDATE PROFILE.
   Flag any bullet that claims a technology, achievement, project, metric, or responsibility
   not explicitly present in the source material.
2. ENTRY COUNT: The number of work_history entries must equal exactly the number in CANDIDATE
   PROFILE. Flag additions, removals, or splits of entries.
3. FACTUAL MUTATIONS: Company names, roles, start_date, end_date, degrees, and institutions
   must match the CANDIDATE PROFILE exactly — character for character. Flag any deviation.
4. UNGROUNDED KEYWORD GAPS: Keyword gaps may only appear in the output where they are
   explicitly supported by the candidate's work history or skills. Flag any keyword added
   without clear supporting evidence in the source material.

Respond ONLY with a valid JSON object — no markdown, no explanations:
{
  "approved": true or false,
  "issues": ["list of specific issues with work_history index and description — empty array if approved"],
  "feedback": "concise instruction for the tailoring agent to correct all issues — empty string if approved"
}"""


def build_review_prompt(source_material: str, tailored_json: dict) -> str:
    """Build the reviewer user prompt for CV tailoring.

    Args:
        source_material: The candidate's master profile JSON serialised as a string.
                         This is the only authoritative source of facts.
        tailored_json: The tailored CV JSON produced by the tailoring agent.
    """
    return (
        "Review this tailored CV against the candidate's source material.\n\n"
        f"CANDIDATE PROFILE (source of truth):\n{source_material}\n\n"
        f"TAILORED CV:\n{json.dumps(tailored_json, ensure_ascii=False, indent=2)}\n\n"
        "Does the tailored CV contain only claims grounded in the source material — "
        "no fabricated bullets, no extra entries, no mutated facts? Return your review JSON."
    )
```

- [ ] **Step 4: Run CV tailoring review tests**

```bash
pytest tests/unit/test_review_prompts.py::TestCVTailoringReviewPrompts -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/applire/prompts/review_cv_tailoring.py tests/unit/test_review_prompts.py
git commit -m "feat(review): add CV tailoring reviewer prompt (ADR-021)"
```

---

## Task 7: Harden `prompts/cv_tailoring.py` to v2

**Files:**
- Modify: `backend/applire/prompts/cv_tailoring.py`
- Modify: `tests/unit/test_review_prompts.py`

- [ ] **Step 1: Write the failing smoke tests**

Append to `tests/unit/test_review_prompts.py`:

```python
_SAMPLE_JOB = {
    "role_title": "Backend Engineer",
    "required_skills": ["Python", "FastAPI"],
    "nice_to_have_skills": ["Kubernetes"],
    "keywords": ["microservices"],
    "seniority_level": "Senior",
    "company_culture_signals": [],
    "language_requirement": "German",
}


class TestCVTailoringGeneratorPrompts:
    def test_build_user_prompt_returns_nonempty_string(self):
        from applire.prompts.cv_tailoring import build_user_prompt

        result = build_user_prompt(_SAMPLE_JOB, _SAMPLE_PROFILE, [], [])
        assert isinstance(result, str)
        assert "Backend Engineer" in result

    def test_build_retry_prompt_includes_feedback(self):
        from applire.prompts.cv_tailoring import build_retry_prompt

        result = build_retry_prompt(
            job_analysis=_SAMPLE_JOB,
            profile_json_str=_SAMPLE_SOURCE_MATERIAL,
            previous_draft=_SAMPLE_TAILORED_CV,
            feedback="Remove fabricated Kubernetes bullet in work_history[0]",
        )
        assert "Remove fabricated Kubernetes bullet" in result
        assert "Backend Engineer" in result

    def test_build_retry_prompt_includes_previous_draft(self):
        from applire.prompts.cv_tailoring import build_retry_prompt

        result = build_retry_prompt(
            job_analysis=_SAMPLE_JOB,
            profile_json_str=_SAMPLE_SOURCE_MATERIAL,
            previous_draft=_SAMPLE_TAILORED_CV,
            feedback="fix",
        )
        assert "Experienced developer" in result  # from summary in _SAMPLE_TAILORED_CV
```

- [ ] **Step 2: Run to confirm tests fail**

```bash
pytest tests/unit/test_review_prompts.py::TestCVTailoringGeneratorPrompts -v
```

Expected: `FAILED` — `build_retry_prompt` not yet defined.

- [ ] **Step 3: Replace `backend/applire/prompts/cv_tailoring.py`**

```python
# Prompt version: v2
# Used by: services/cv.py → LLMProvider.aparse_json + reviewer.review_and_refine
# Changes from v1: Rules 1, 3, 5 hardened against hallucination;
#                  Rule 6 added (entry count constraint);
#                  Rule 7 added (language, was Rule 6);
#                  build_retry_prompt added for review layer retries.

import json

SYSTEM_PROMPT = """\
You are an expert DACH career consultant specialising in writing tailored German CVs (Lebenslauf).
Your task is to rewrite a candidate's profile to maximise fit for a specific job, following these rules:

1. Rephrase and re-emphasise bullets already in CANDIDATE PROFILE to highlight relevance to the job.
   Use strong action verbs. Do NOT add new achievements, technologies, projects, or metrics that are
   not explicitly present in CANDIDATE PROFILE. Quantify only where CANDIDATE PROFILE explicitly
   provides numbers or metrics — never infer or invent figures.
2. Reorder work history to surface the most relevant experience first
   (reverse-chronological within relevance tier).
3. Filter and reorder the skills list to lead with skills explicitly required in the job description.
   Keyword gaps may ONLY be incorporated if they are explicitly demonstrated in the candidate's
   work history or skills list. If a keyword gap has no explicit basis in CANDIDATE PROFILE, omit it.
4. Write a concise professional summary (2–3 sentences, third person) tailored to the role.
5. Keep all factual data EXACTLY as provided — company names, roles, dates, degrees, technologies,
   project names, and metrics. Do NOT invent, infer, or embellish ANY fact not present in
   CANDIDATE PROFILE. When in doubt, leave it out.
6. The number of work_history entries in your output must equal exactly the number in CANDIDATE
   PROFILE. Do not add, remove, or split entries.
7. Output language: match the job description language (German if German JD, English otherwise).

Respond ONLY with a valid JSON object matching this schema — no markdown, no explanations:

{
  "contact": {
    "name": string,
    "email": string or null,
    "phone": string or null,
    "location": string or null,
    "linkedin": string or null
  },
  "summary": string,
  "work_history": [
    {
      "company": string,
      "role": string,
      "start_date": string,
      "end_date": string or null,
      "bullets": [string]
    }
  ],
  "skills": [string],
  "education": [
    {
      "institution": string,
      "degree": string,
      "field": string,
      "start_date": string,
      "end_date": string or null
    }
  ],
  "languages": [
    {"language": string, "level": string}
  ]
}"""


def build_user_prompt(
    job_analysis: dict,
    profile: dict,
    keyword_gaps: list[str],
    critical_gaps: list[str],
) -> str:
    return (
        "Tailor the candidate's profile for the job below.\n\n"
        f"JOB ANALYSIS:\n{json.dumps(job_analysis, ensure_ascii=False, indent=2)}\n\n"
        f"CANDIDATE PROFILE:\n{json.dumps(profile, ensure_ascii=False, indent=2)}\n\n"
        f"KEYWORD GAPS (incorporate only where explicitly supported by profile):\n"
        f"{json.dumps(keyword_gaps, ensure_ascii=False)}\n\n"
        f"CRITICAL GAPS (acknowledge in summary if applicable):\n"
        f"{json.dumps(critical_gaps, ensure_ascii=False)}\n\n"
        "Return the tailored CV JSON."
    )


def build_retry_prompt(
    job_analysis: dict,
    profile_json_str: str,
    previous_draft: dict,
    feedback: str,
) -> str:
    """Build the retry user prompt after a reviewer rejection.

    Args:
        job_analysis: The structured job analysis dict (same as initial call).
        profile_json_str: The candidate's master profile serialised as a JSON string.
        previous_draft: The tailored CV the reviewer rejected.
        feedback: The reviewer's critique — used verbatim as the correction instruction.
    """
    return (
        "A quality review of your previous CV tailoring identified the following issues. "
        "Correct them and return the updated JSON.\n\n"
        f"REVIEW FEEDBACK:\n{feedback}\n\n"
        f"PREVIOUS OUTPUT:\n{json.dumps(previous_draft, ensure_ascii=False, indent=2)}\n\n"
        f"JOB ANALYSIS:\n{json.dumps(job_analysis, ensure_ascii=False, indent=2)}\n\n"
        f"CANDIDATE PROFILE (the only source of truth for facts):\n{profile_json_str}\n\n"
        "Return the corrected tailored CV JSON."
    )
```

- [ ] **Step 4: Run all prompt tests**

```bash
pytest tests/unit/test_review_prompts.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/prompts/cv_tailoring.py tests/unit/test_review_prompts.py
git commit -m "feat(review): harden cv_tailoring prompt to v2, add build_retry_prompt"
```

---

## Task 8: Integrate review into `services/cv.py`

**Files:**
- Modify: `backend/applire/services/cv.py`
- Modify: `tests/unit/test_review_prompts.py`

- [ ] **Step 1: Write the integration test**

Append to `tests/unit/test_review_prompts.py`:

```python
class TestCVServiceReviewIntegration:
    """Verify that _render_cv_background calls review_and_refine with correct arguments."""

    @pytest.mark.asyncio
    async def test_render_cv_background_passes_profile_as_source(self):
        """review_and_refine source should be the serialised master profile JSON."""
        import json
        import uuid
        from unittest.mock import AsyncMock, MagicMock, patch

        profile_json = {
            "work_history": [{"company": "Acme", "role": "Dev", "start_date": "2020", "end_date": None, "bullets": []}],
            "skills": ["Python"],
            "education": [],
            "languages": [],
            "contact": {"name": "Max", "email": None, "phone": None, "location": None, "linkedin": None},
            "personal_info": {},
        }

        tailored_raw = {
            "contact": {"name": "Max", "email": None, "phone": None, "location": None, "linkedin": None},
            "summary": "Dev.",
            "work_history": [{"company": "Acme", "role": "Dev", "start_date": "2020", "end_date": None, "bullets": []}],
            "skills": ["Python"],
            "education": [],
            "languages": [],
        }

        captured: dict = {}

        async def fake_review(**kwargs):
            captured.update(kwargs)
            return kwargs["draft"]

        mock_cv_id = uuid.uuid4()
        mock_job_id = uuid.uuid4()
        mock_profile_id = uuid.uuid4()

        mock_cv = MagicMock()
        mock_cv.status = "pending"
        mock_job = MagicMock()
        mock_job.role_title = "Dev"
        mock_job.required_skills = []
        mock_job.nice_to_have_skills = []
        mock_job.keywords = []
        mock_job.seniority_level = ""
        mock_job.company_culture_signals = []
        mock_job.language_requirement = ""
        mock_profile = MagicMock()
        mock_profile.profile_json = profile_json

        mock_db = AsyncMock()
        mock_db.get.side_effect = lambda model, id_: {
            mock_cv_id: mock_cv,
            mock_job_id: mock_job,
            mock_profile_id: mock_profile,
        }[id_]
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        mock_provider = AsyncMock()
        mock_provider.aparse_json.return_value = tailored_raw

        with patch("applire.services.cv.AsyncSessionLocal") as mock_session_local, \
             patch("applire.services.cv.get_provider", return_value=mock_provider), \
             patch("applire.services.cv.review_and_refine", side_effect=fake_review), \
             patch("applire.services.cv.LLM_REVIEW_MAX_RETRIES", 2), \
             patch("applire.services.cv._html_to_pdf", new=AsyncMock(return_value=b"pdf")), \
             patch("applire.services.cv.build_content_snapshot", return_value={}), \
             patch("applire.services.cv.get_storage"):
            mock_session_local.return_value.__aenter__.return_value = mock_db
            from applire.services.cv import _render_cv_background
            await _render_cv_background(mock_cv_id, mock_job_id, mock_profile_id, "classic_german")

        expected_source = json.dumps(profile_json, ensure_ascii=False, indent=2)
        assert captured.get("source") == expected_source
        assert captured.get("draft") == tailored_raw
        assert captured.get("max_retries") == 2
```

- [ ] **Step 2: Run to confirm the test fails**

```bash
pytest tests/unit/test_review_prompts.py::TestCVServiceReviewIntegration -v
```

Expected: `FAILED` — `review_and_refine` not yet imported in `cv.py`.

- [ ] **Step 3: Update `backend/applire/services/cv.py`**

Add these imports after the existing imports:

```python
import json as _json

from applire.constants import LLM_REVIEW_MAX_RETRIES
from applire.prompts.cv_tailoring import build_retry_prompt as _build_cv_retry_prompt
from applire.prompts.review_cv_tailoring import (
    REVIEW_SYSTEM_PROMPT as _CV_REVIEW_SYSTEM_PROMPT,
    build_review_prompt as _build_cv_review_prompt,
)
from applire.services.reviewer import review_and_refine
```

In `_render_cv_background`, replace the block that calls `provider.aparse_json` and validates `tailored_raw` with:

```python
            tailored_raw: dict = await provider.aparse_json(
                build_user_prompt(job_dict, profile.profile_json, keyword_gaps, critical_gaps),
                system=SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=8192,
            )

            source_material = _json.dumps(profile.profile_json, ensure_ascii=False, indent=2)

            def _cv_retry_prompt(source: str, draft: dict, feedback: str) -> str:
                return _build_cv_retry_prompt(job_dict, source, draft, feedback)

            tailored_raw = await review_and_refine(
                source=source_material,
                draft=tailored_raw,
                generator_prompt_fn=_cv_retry_prompt,
                generator_system=SYSTEM_PROMPT,
                reviewer_prompt_fn=_build_cv_review_prompt,
                reviewer_system=_CV_REVIEW_SYSTEM_PROMPT,
                provider=provider,
                max_retries=LLM_REVIEW_MAX_RETRIES,
            )

            tailored = TailoredCVData.model_validate(tailored_raw)
```

- [ ] **Step 4: Run all unit tests**

```bash
pytest tests/unit/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/cv.py tests/unit/test_review_prompts.py
git commit -m "feat(review): integrate review_and_refine into CV tailoring service"
```

---

## Task 9: Document env var in docker-compose.yml and run full test suite

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add commented env var to docker-compose.yml**

Find the `backend` service's `environment:` block in `docker-compose.yml` and add the commented entry alongside the existing interview config:

```yaml
      # LLM review layer — max generator retries per reviewed step (0 = disabled).
      # Increase to 3 for higher quality at the cost of more LLM tokens.
      # LLM_REVIEW_MAX_RETRIES=2
```

- [ ] **Step 2: Run the full unit test suite with coverage**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ -v --cov=applire --cov-report=term-missing
```

Expected: all tests pass, coverage ≥ 75%.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "docs(review): document LLM_REVIEW_MAX_RETRIES env var in docker-compose.yml"
```

- [ ] **Step 4: Final integration smoke check**

Confirm the entire backend imports cleanly:

```bash
cd /home/apliqa/Documents/Applire/Solution/backend
python -c "
from applire.services.reviewer import review_and_refine
from applire.prompts.review_profile_extraction import REVIEW_SYSTEM_PROMPT, build_review_prompt
from applire.prompts.review_cv_tailoring import REVIEW_SYSTEM_PROMPT as R2, build_review_prompt as b2
from applire.constants import LLM_REVIEW_MAX_RETRIES
print('All imports OK. max_retries =', LLM_REVIEW_MAX_RETRIES)
"
```

Expected: `All imports OK. max_retries = 2`
