# Gap-View Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat gap list (up to 50 items) with semantic clusters (5–12), add JD context, multiple-choice questions, and a split-screen interview UI.

**Architecture:** A second LLM step (`cluster_gaps()`) runs after `analyze_gaps()` and stores clusters in a new `gap_analyses.gap_clusters` JSONB column. The interview graph is updated to navigate by cluster ID instead of gap string. The frontend gaps page shows cluster cards; the interview page becomes a 65/35 split screen with a right-panel cluster tracker.

**Tech Stack:** Python/FastAPI/SQLAlchemy/Alembic, Pydantic v2, Next.js 15/React 19/TypeScript/Tailwind CSS v4/next-intl, pytest (SQLite in-memory).

---

## File Map

### New files
- `backend/alembic/versions/0027_gap_clusters.py`
- `backend/applire/schemas/gap_cluster.py`
- `backend/applire/prompts/gap_clustering.py`
- `tests/unit/test_gap_clustering.py`
- `frontend/components/gaps/GapClusterCard.tsx`

### Modified files
- `backend/applire/models/gap.py` — add `gap_clusters` column
- `backend/applire/schemas/gap.py` — add `gap_clusters` field to `GapAnalysisResponse`
- `backend/applire/schemas/session.py` — add `choices`, remove `gaps_also_addressed`, add `gap_clusters_by_id` to `InterviewState`
- `backend/applire/prompts/interview.py` — JSON question output, cluster-aware prompt, remove cross-gap from response parser
- `backend/applire/services/gap.py` — add `cluster_gaps()`, call it from `_run_analysis()`
- `backend/applire/services/interview_graph.py` — `gap_detector()` returns 3-tuple; `question_generator_with_profile()` returns dict; `response_parser()` removes `remaining_gaps`/`gaps_also_addressed`
- `backend/applire/services/session.py` — thread `choices`; remove cross-gap block; micro-session uses cluster lookup; `_build_state` adds `gap_clusters_by_id`
- `tests/unit/test_gap_analysis.py` — fix `gap_detector` tuple-unpack (2 → 3 values)
- `tests/unit/test_interview_service.py` — fix `response_parser` calls, remove `gaps_also_addressed` assertions, fix `question_generator_with_profile` return type assertions
- `tests/unit/test_response_parser.py` — fix `gap_detector` tuple-unpack
- `tests/unit/test_enrich_response_parser_review.py` — remove `gaps_also_addressed` from mock
- `frontend/messages/de.json` — add cluster i18n keys
- `frontend/messages/en.json` — add cluster i18n keys
- `frontend/app/flow/[flowId]/gaps/page.tsx` — cluster card layout, extended GapClickPanel
- `frontend/app/flow/[flowId]/interview/page.tsx` — split-screen redesign

---

## Task 1: DB Migration + ORM model

**Files:**
- Create: `backend/alembic/versions/0027_gap_clusters.py`
- Modify: `backend/applire/models/gap.py`

- [ ] **Step 1: Create migration file**

```python
# backend/alembic/versions/0027_gap_clusters.py
"""Add gap_clusters JSONB column to gap_analyses

Revision ID: 0027
Revises: 0026
Create Date: 2026-04-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0027"
down_revision: Union[str, None] = "0026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "gap_analyses",
        sa.Column(
            "gap_clusters",
            JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("gap_analyses", "gap_clusters")
```

- [ ] **Step 2: Add column to ORM model**

In `backend/applire/models/gap.py`, add after `category_c`:

```python
    gap_clusters: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
```

- [ ] **Step 3: Run migration**

```bash
cd backend && alembic upgrade head
```

Expected: `Running upgrade 0026 -> 0027, Add gap_clusters JSONB column to gap_analyses`

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/0027_gap_clusters.py backend/applire/models/gap.py
git commit -m "feat: add gap_clusters JSONB column to gap_analyses (migration 0027)"
```

---

## Task 2: GapCluster Pydantic schema + extend GapAnalysisResponse

**Files:**
- Create: `backend/applire/schemas/gap_cluster.py`
- Modify: `backend/applire/schemas/gap.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_gap_clustering.py
"""Unit tests for gap clustering schema and service."""
from applire.schemas.gap_cluster import GapClusterSchema


def test_gap_cluster_schema_validates():
    raw = {
        "id": "cluster-agentic",
        "label": "Agentic AI Systems",
        "category": "C",
        "gaps": ["Agentic Systems", "AI Systems"],
        "jd_skills": ["LLM-based Agent Design"],
        "jd_context": "Die Stelle sucht jemanden, der autonome KI-Agenten designt.",
    }
    cluster = GapClusterSchema.model_validate(raw)
    assert cluster.id == "cluster-agentic"
    assert cluster.category == "C"
    assert len(cluster.gaps) == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_gap_clustering.py::test_gap_cluster_schema_validates -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'applire.schemas.gap_cluster'`

- [ ] **Step 3: Create GapClusterSchema**

```python
# backend/applire/schemas/gap_cluster.py
from typing import Literal

from pydantic import BaseModel


class GapClusterSchema(BaseModel):
    id: str
    label: str
    category: Literal["B", "C"]
    gaps: list[str]
    jd_skills: list[str]
    jd_context: str
```

- [ ] **Step 4: Extend GapAnalysisResponse**

In `backend/applire/schemas/gap.py`, add import and field:

```python
# At top of file, add import:
from applire.schemas.gap_cluster import GapClusterSchema

# In GapAnalysisResponse class, after category_c field:
    gap_clusters: list[GapClusterSchema] = Field(default_factory=list)
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_gap_clustering.py::test_gap_cluster_schema_validates -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/applire/schemas/gap_cluster.py backend/applire/schemas/gap.py tests/unit/test_gap_clustering.py
git commit -m "feat: add GapClusterSchema and extend GapAnalysisResponse with gap_clusters"
```

---

## Task 3: Gap clustering prompt

**Files:**
- Create: `backend/applire/prompts/gap_clustering.py`

- [ ] **Step 1: Write failing test for the prompt builder**

In `tests/unit/test_gap_clustering.py`, append:

```python
def test_build_clustering_prompt_includes_gaps():
    from applire.prompts.gap_clustering import build_clustering_prompt
    prompt = build_clustering_prompt(
        category_b=["Python basics", "Git"],
        category_c=["LLMs", "Agentic Systems", "AI Systems"],
        required_skills=["LLM-based Agent Design", "Python"],
        nice_to_have_skills=["Multi-Agent Orchestration"],
    )
    assert "LLMs" in prompt
    assert "Agentic Systems" in prompt
    assert "LLM-based Agent Design" in prompt
    assert "Python basics" in prompt


def test_clustering_system_prompt_exists():
    from applire.prompts.gap_clustering import CLUSTERING_SYSTEM_PROMPT
    assert "cluster" in CLUSTERING_SYSTEM_PROMPT.lower()
    assert "JSON" in CLUSTERING_SYSTEM_PROMPT
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_gap_clustering.py -k "prompt" -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create the prompt file**

```python
# backend/applire/prompts/gap_clustering.py
# Prompt version: v1
# Used by: services/gap.py (cluster_gaps)

import json

CLUSTERING_SYSTEM_PROMPT = """\
You are an expert career analyst. Your task is to group semantically related skill gaps into \
named clusters for a DACH job applicant.

Input: lists of Category B and Category C gaps from a gap analysis, plus the job's required and \
nice-to-have skills.

Output: a JSON array of cluster objects. Each cluster absorbs multiple gaps that share the same \
semantic domain.

Schema for each cluster object:
{
  "id": "cluster-<label-kebab-lowercase>",
  "label": "Human-readable cluster name (concise, 2-5 words)",
  "category": "C or B (C if any member gap is Category C, else B)",
  "gaps": ["exact gap strings absorbed into this cluster"],
  "jd_skills": ["matching entries from required_skills or nice_to_have_skills"],
  "jd_context": "One sentence, first-person role perspective, in the language of the job description, explaining why this cluster matters for the role."
}

Rules:
- Merge gaps that share the same semantic domain (not just keywords)
- category = "C" if any constituent gap is Category C, else "B"
- jd_skills: only include skills that directly motivate this cluster (may be empty)
- jd_context: one sentence, written in the same language as the job description (German or English)
- Target 5–12 clusters; never more clusters than input gaps
- Every input gap must appear in exactly one cluster
- Respond ONLY with a valid JSON array — no markdown, no explanations"""


def build_clustering_prompt(
    category_b: list[str],
    category_c: list[str],
    required_skills: list[str],
    nice_to_have_skills: list[str],
) -> str:
    return (
        f"Category C gaps (missing evidence):\n{json.dumps(category_c, ensure_ascii=False)}\n\n"
        f"Category B gaps (likely but unstated):\n{json.dumps(category_b, ensure_ascii=False)}\n\n"
        f"Required skills from JD:\n{json.dumps(required_skills, ensure_ascii=False)}\n\n"
        f"Nice-to-have skills from JD:\n{json.dumps(nice_to_have_skills, ensure_ascii=False)}\n\n"
        "Group the gaps into semantic clusters. Return a JSON array."
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_gap_clustering.py -k "prompt" -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/applire/prompts/gap_clustering.py tests/unit/test_gap_clustering.py
git commit -m "feat: add gap_clustering prompt with system prompt and build_clustering_prompt"
```

---

## Task 4: cluster_gaps() service + integrate into _run_analysis()

**Files:**
- Modify: `backend/applire/services/gap.py`
- Test: `tests/unit/test_gap_clustering.py`

- [ ] **Step 1: Write failing test for cluster_gaps()**

In `tests/unit/test_gap_clustering.py`, append:

```python
import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest


@pytest.mark.asyncio
async def test_cluster_gaps_persists_clusters():
    """cluster_gaps() calls LLM and saves result to gap_analysis.gap_clusters."""
    from applire.services.gap import cluster_gaps
    from applire.models.gap import GapAnalysis
    from applire.models.job import JobAnalysis

    gap_analysis = MagicMock(spec=GapAnalysis)
    gap_analysis.category_b = ["Python basics"]
    gap_analysis.category_c = ["LLMs", "Agentic Systems"]

    job = MagicMock(spec=JobAnalysis)
    job.required_skills = ["LLM-based Agent Design"]
    job.nice_to_have_skills = ["Multi-Agent Orchestration"]

    clusters_raw = [
        {
            "id": "cluster-agentic",
            "label": "Agentic AI Systems",
            "category": "C",
            "gaps": ["LLMs", "Agentic Systems"],
            "jd_skills": ["LLM-based Agent Design"],
            "jd_context": "The role requires designing autonomous AI agents.",
        },
        {
            "id": "cluster-python",
            "label": "Python Fundamentals",
            "category": "B",
            "gaps": ["Python basics"],
            "jd_skills": [],
            "jd_context": "Python is used throughout the stack.",
        },
    ]

    provider = MagicMock()
    provider.aparse_json = AsyncMock(return_value=clusters_raw)

    db = MagicMock()
    db.commit = AsyncMock()

    await cluster_gaps(gap_analysis, job, provider, db)

    assert gap_analysis.gap_clusters == clusters_raw
    db.commit.assert_awaited_once()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_gap_clustering.py::test_cluster_gaps_persists_clusters -v
```

Expected: FAIL — `ImportError` or `AttributeError`

- [ ] **Step 3: Add cluster_gaps() to services/gap.py**

At the top of `backend/applire/services/gap.py`, add imports after existing imports:

```python
from applire.prompts.gap_clustering import CLUSTERING_SYSTEM_PROMPT, build_clustering_prompt
from applire.schemas.gap_cluster import GapClusterSchema
```

Add the new function after `analyze_gaps_for_session()`:

```python
async def cluster_gaps(
    gap_analysis: GapAnalysis,
    job: JobAnalysis,
    provider: LLMProvider,
    db: AsyncSession,
) -> None:
    """Run clustering LLM call and persist result to gap_analysis.gap_clusters."""
    raw_clusters: list = await provider.aparse_json(
        build_clustering_prompt(
            category_b=list(gap_analysis.category_b or []),
            category_c=list(gap_analysis.category_c or []),
            required_skills=list(job.required_skills or []),
            nice_to_have_skills=list(job.nice_to_have_skills or []),
        ),
        system=CLUSTERING_SYSTEM_PROMPT,
        temperature=0.1,
    )
    # Validate each cluster — silently drop malformed entries
    validated = []
    for item in (raw_clusters if isinstance(raw_clusters, list) else []):
        try:
            validated.append(GapClusterSchema.model_validate(item).model_dump())
        except Exception:
            pass
    gap_analysis.gap_clusters = validated
    await db.commit()
```

- [ ] **Step 4: Integrate cluster_gaps() into _run_analysis()**

In `_run_analysis()`, replace the final block (after `await db.refresh(record)`) with:

```python
    db.add(record)
    await db.commit()
    await db.refresh(record)

    # Phase 2: semantic clustering
    await cluster_gaps(record, job, provider, db)
    await db.refresh(record)

    return GapAnalysisResponse.model_validate(record)
```

Also update the `_run_analysis` signature to accept `job: JobAnalysis` (it already does) and the call sites in `analyze_gaps` already pass `job` — verify the internal call is:

```python
    return await _run_analysis(job, profile, db, provider)
```

That is correct already — `job` is the first argument.

- [ ] **Step 5: Run test to verify it passes**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_gap_clustering.py::test_cluster_gaps_persists_clusters -v
```

Expected: PASS

- [ ] **Step 6: Run all clustering tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_gap_clustering.py -v
```

Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add backend/applire/services/gap.py tests/unit/test_gap_clustering.py
git commit -m "feat: add cluster_gaps() and integrate into _run_analysis() as phase-2 step"
```

---

## Task 5: Update schemas/session.py

**Files:**
- Modify: `backend/applire/schemas/session.py`

- [ ] **Step 1: Add `choices` to SessionCreateResponse**

Replace the `SessionCreateResponse` class definition with:

```python
class SessionCreateResponse(BaseModel):
    session_id: uuid.UUID
    mode: Literal["targeted", "guided"]
    first_question: str
    estimated_questions: int
    question: str  # same as first_question — legacy field
    gaps_total: int
    gaps_remaining: int
    choices: list[str] | None = None
    resumed: bool = False
```

- [ ] **Step 2: Update SessionMessageResponse — add choices, remove gaps_also_addressed**

Replace the `SessionMessageResponse` class definition with:

```python
class SessionMessageResponse(BaseModel):
    complete: bool
    question: str | None = None
    gaps_remaining: int | None = None
    choices: list[str] | None = None
    # Populated when complete=True
    reason: Literal["gaps_resolved", "user_ended", "max_questions_reached"] | None = None
    questions_asked: int | None = None
    gaps_resolved: int | None = None
    gaps_unresolved: list[str] | None = None
    completeness_score: float | None = None
    # Populated when ProfileUpdater detects a merge conflict (19.10)
    pending_conflicts: list[ConflictSummary] | None = None
```

- [ ] **Step 3: Update InterviewState TypedDict — add gap_clusters_by_id**

Replace the `InterviewState` TypedDict with:

```python
class InterviewState(TypedDict):
    mode: str  # "targeted" | "guided" | "profile_enrich"
    job_id: str | None
    gap_analysis_id: str | None
    profile_id: str
    # MODE A: ordered cluster IDs (C-first, then B)
    # MODE B: ordered section names to build
    critical_gaps: list[str]
    gap_categories: dict  # {cluster_id: "B" | "C"} — empty dict for MODE B
    gap_clusters_by_id: dict  # {cluster_id: GapCluster dict} — empty for MODE B
    addressed_gaps: list[str]
    current_gap_index: int
    current_question: str
    current_choices: list | None  # choices for current question (None = text-only)
    messages: list[dict]
    questions_asked: int
    hard_ceiling: int
    questions_per_gap: dict
    skipped_gaps: list[str]
    full_gaps: list[str]
    na_gaps: list[str]
```

- [ ] **Step 4: Commit**

```bash
git add backend/applire/schemas/session.py
git commit -m "feat: add choices to session schemas, remove gaps_also_addressed, add gap_clusters_by_id to InterviewState"
```

---

## Task 6: Update prompts/interview.py

**Files:**
- Modify: `backend/applire/prompts/interview.py`

Changes: `QUESTION_SYSTEM_PROMPT` outputs JSON; `build_question_prompt` takes a `cluster: dict`; `RESPONSE_PARSER_SYSTEM_PROMPT` removes `gaps_also_addressed`; `build_response_parser_prompt` drops `remaining_gaps`.

- [ ] **Step 1: Replace QUESTION_SYSTEM_PROMPT**

```python
QUESTION_SYSTEM_PROMPT = """\
You are an expert career coach specialised in the DACH (Germany, Austria, Switzerland) job market.
Your task is to generate ONE targeted, open-ended question to help a job seeker articulate concrete \
experience that addresses a specific skill cluster gap in their profile.

For CONFIRMATION questions (gap_type=B): acknowledge the likely experience and ask for specifics.
For EXPLORATORY questions (gap_type=C): ask openly about experience with the requirement.

Generate 2–3 short answer choices when:
- The cluster has 2 or more constituent gaps, OR
- The cluster category is B (confirmation question)
Choices are starting-point options the candidate can select and expand; they are not exhaustive.
Otherwise set choices to null.

Requirements:
- Ask about exactly ONE aspect related to the cluster
- Be encouraging and conversational in tone
- Invite specific examples: projects, companies, dates, measurable outcomes
- Output ONLY a valid JSON object — no markdown, no explanations

Schema:
{
  "question": "The question text",
  "choices": ["Option A", "Option B"] or null
}"""
```

- [ ] **Step 2: Replace build_question_prompt to accept cluster dict**

```python
def build_question_prompt(
    cluster: dict,
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

    cluster_label = cluster.get("label", cluster.get("id", "unknown"))
    constituent_gaps = cluster.get("gaps", [])
    jd_skills = cluster.get("jd_skills", [])
    jd_context = cluster.get("jd_context", "")
    num_gaps = len(constituent_gaps)

    if gap_category == "B":
        gap_type_hint = (
            f"Gap type: CONFIRMATION (Category B) — "
            f"the system inferred the candidate likely has experience with '{cluster_label}'. "
            f"Generate a confirmation question that acknowledges this likelihood and asks for concrete specifics."
        )
    else:
        gap_type_hint = (
            f"Gap type: EXPLORATORY (Category C) — "
            f"no signal for '{cluster_label}' was found in the profile. "
            f"Generate an open question to uncover any relevant experience."
        )

    choices_hint = (
        f"Generate 2–3 choices (num_gaps={num_gaps}, category={gap_category or 'C'})."
        if (num_gaps >= 2 or gap_category == "B")
        else "Set choices to null."
    )

    cluster_context = f"Cluster: {cluster_label}"
    if constituent_gaps:
        cluster_context += f"\nConstituent gaps: {', '.join(constituent_gaps)}"
    if jd_skills:
        cluster_context += f"\nRelevant JD skills: {', '.join(jd_skills)}"
    if jd_context:
        cluster_context += f"\nJD context: {jd_context}"

    return (
        f"{cluster_context}\n"
        f"{gap_type_hint}\n"
        f"{choices_hint}\n\n"
        f"Candidate profile summary:\n{profile_summary}"
        f"{history}\n\n"
        "Generate the JSON response."
    )
```

- [ ] **Step 3: Update RESPONSE_PARSER_SYSTEM_PROMPT — remove gaps_also_addressed**

Replace `RESPONSE_PARSER_SYSTEM_PROMPT` with:

```python
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
  "follow_up_hint": "Short suggestion for adjacent domain to probe, or null"
}

Rules:
- Only include data EXPLICITLY stated in the answer — do not infer or fabricate
- gap_resolution: "full" if the answer provides concrete, specific information about the gap;
  "partial" if relevant but incomplete or vague; "none" if off-topic or empty
- follow_up_hint: when gap_resolution is "partial" or "none", suggest a related domain or context
  the candidate might have experience in. Set to null when gap_resolution is "full".
- Omit work_history_to_add entries where role is null or empty"""
```

- [ ] **Step 4: Update build_response_parser_prompt — remove remaining_gaps parameter**

```python
def build_response_parser_prompt(
    cluster_label: str,
    question: str,
    answer: str,
) -> str:
    return (
        f"Gap cluster being addressed: {cluster_label}\n\n"
        f"Question asked: {question}\n\n"
        f"Candidate's answer: {answer}\n\n"
        "Extract the structured profile data."
    )
```

- [ ] **Step 5: Commit**

```bash
git add backend/applire/prompts/interview.py
git commit -m "feat: update interview prompts for cluster-aware questions and remove cross-gap response parser"
```

---

## Task 7: Update interview_graph.py

**Files:**
- Modify: `backend/applire/services/interview_graph.py`

Changes: `gap_detector()` returns 3-tuple; `question_generator_with_profile()` returns dict; `response_parser()` simplified.

- [ ] **Step 1: Replace gap_detector() function**

```python
def gap_detector(
    gap_analysis: GapAnalysis,
) -> tuple[list[str], dict[str, str], dict]:
    """Return (ordered_cluster_ids, cluster_categories, clusters_by_id).

    Ordered C-first, then B. Reads from gap_analysis.gap_clusters.
    """
    clusters: list[dict] = list(gap_analysis.gap_clusters or [])
    c_clusters = [c for c in clusters if c.get("category") == "C"]
    b_clusters = [c for c in clusters if c.get("category") == "B"]
    ordered = c_clusters + b_clusters

    cluster_ids = [c["id"] for c in ordered]
    categories = {c["id"]: c["category"] for c in ordered}
    by_id = {c["id"]: c for c in ordered}
    return cluster_ids, categories, by_id
```

- [ ] **Step 2: Update question_generator_with_profile() return type to dict**

Replace the entire function:

```python
async def question_generator_with_profile(
    state: InterviewState,
    profile: dict,
    provider: LLMProvider,
    gap_category: str | None = None,
    job_context: dict | None = None,
    follow_up_hint: str | None = None,
) -> dict:
    """Generate the next question based on mode and context.

    Returns:
        {"question": str, "choices": list[str] | None}
    """
    mode = state.get("mode", "targeted")

    if follow_up_hint:
        cluster_id = state["critical_gaps"][state["current_gap_index"]]
        clusters_by_id = state.get("gap_clusters_by_id") or {}
        cluster = clusters_by_id.get(cluster_id, {"label": cluster_id, "gaps": []})
        gap_label = cluster.get("label", cluster_id)
        text = await provider.acomplete(
            build_follow_up_question_prompt(
                gap_label,
                follow_up_hint,
                profile,
                state["messages"],
                gap_category=gap_category,
            ),
            system=FOLLOW_UP_QUESTION_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=256,
        )
        return {"question": text.strip(), "choices": None}

    if mode == "guided":
        section = state["critical_gaps"][state["current_gap_index"]]
        text = await provider.acomplete(
            build_guided_question_prompt(
                section,
                job_context or {},
                state["messages"],
            ),
            system=GUIDED_QUESTION_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=256,
        )
        return {"question": text.strip(), "choices": None}

    # MODE A: cluster-aware question with potential choices
    cluster_id = state["critical_gaps"][state["current_gap_index"]]
    clusters_by_id = state.get("gap_clusters_by_id") or {}
    cluster = clusters_by_id.get(cluster_id, {"id": cluster_id, "label": cluster_id, "gaps": [], "jd_skills": [], "jd_context": ""})

    data: dict = await provider.aparse_json(
        build_question_prompt(cluster, profile, state["messages"], gap_category=gap_category),
        system=QUESTION_SYSTEM_PROMPT,
        temperature=0.4,
    )
    question = str(data.get("question", "")).strip()
    raw_choices = data.get("choices")
    choices = raw_choices if isinstance(raw_choices, list) and raw_choices else None
    return {"question": question, "choices": choices}
```

- [ ] **Step 3: Update question_generator() (legacy, no-profile version)**

```python
async def question_generator(
    state: InterviewState,
    provider: LLMProvider,
) -> dict:
    """Generate a targeted question for the current gap (no profile context).

    Kept for backwards compatibility — prefer question_generator_with_profile.
    Returns: {"question": str, "choices": None}
    """
    cluster_id = state["critical_gaps"][state["current_gap_index"]]
    clusters_by_id = state.get("gap_clusters_by_id") or {}
    cluster = clusters_by_id.get(cluster_id, {"id": cluster_id, "label": cluster_id, "gaps": [], "jd_skills": [], "jd_context": ""})
    data: dict = await provider.aparse_json(
        build_question_prompt(cluster, {}, state["messages"]),
        system=QUESTION_SYSTEM_PROMPT,
        temperature=0.4,
    )
    return {"question": str(data.get("question", "")).strip(), "choices": None}
```

- [ ] **Step 4: Simplify response_parser() — drop remaining_gaps and gaps_also_addressed**

```python
async def response_parser(
    cluster_label: str,
    question: str,
    answer: str,
    provider: LLMProvider,
) -> dict:
    """Extract structured profile data from the user's free-text answer.

    Returns a dict with keys:
        skills_to_add, work_history_to_add, certifications_to_add,
        languages_to_add, education_to_add, gap_resolution, follow_up_hint,
        gap_addressed  (backward compat — derived from gap_resolution != "none")
    """
    data = await provider.aparse_json(
        build_response_parser_prompt(cluster_label, question, answer),
        system=RESPONSE_PARSER_SYSTEM_PROMPT,
        temperature=0.1,
    )
    gap_resolution = data.get("gap_resolution", "none")
    if gap_resolution not in ("full", "partial", "none"):
        gap_resolution = "none"
    return {
        "skills_to_add": data.get("skills_to_add", []),
        "work_history_to_add": data.get("work_history_to_add", []),
        "certifications_to_add": data.get("certifications_to_add", []),
        "languages_to_add": data.get("languages_to_add", []),
        "education_to_add": data.get("education_to_add", []),
        "gap_resolution": gap_resolution,
        "follow_up_hint": data.get("follow_up_hint") if isinstance(data.get("follow_up_hint"), str) else None,
        "gap_addressed": gap_resolution != "none",
    }
```

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/interview_graph.py
git commit -m "feat: update interview_graph — gap_detector returns clusters, question_generator returns dict, response_parser simplified"
```

---

## Task 8: Update services/session.py

**Files:**
- Modify: `backend/applire/services/session.py`

Changes: thread `choices` through all paths; remove cross-gap block; micro-session uses cluster lookup; `_build_state` adds `gap_clusters_by_id`.

- [ ] **Step 1: Update _build_state() to add gap_clusters_by_id and current_choices**

Replace `_build_state` with:

```python
def _build_state(
    *,
    mode: str,
    job_id: uuid.UUID,
    gap_analysis_id: uuid.UUID | None,
    profile_id: uuid.UUID,
    critical_gaps: list[str],
    gap_categories: dict,
    gap_clusters_by_id: dict,
    current_question: str,
    hard_ceiling: int,
) -> InterviewState:
    return {
        "mode": mode,
        "job_id": str(job_id),
        "gap_analysis_id": str(gap_analysis_id) if gap_analysis_id else None,
        "profile_id": str(profile_id),
        "critical_gaps": critical_gaps,
        "gap_categories": gap_categories,
        "gap_clusters_by_id": gap_clusters_by_id,
        "addressed_gaps": [],
        "current_gap_index": 0,
        "current_question": current_question,
        "current_choices": None,
        "messages": [],
        "questions_asked": 0,
        "hard_ceiling": hard_ceiling,
        "questions_per_gap": {},
        "skipped_gaps": [],
        "full_gaps": [],
        "na_gaps": [],
    }
```

- [ ] **Step 2: Update _create_targeted_session() to use gap_detector 3-tuple and propagate choices**

Replace the `_create_targeted_session` function:

```python
async def _create_targeted_session(
    job_id: uuid.UUID,
    job: JobAnalysis,
    profile_record: MasterProfile | None,
    db: AsyncSession,
    provider: LLMProvider,
) -> SessionCreateResponse:
    if profile_record is None:
        raise LookupError(
            "No profile found — upload a CV first, or use mode='guided' to build from scratch"
        )

    # Lazy gap analysis
    gap_result = await db.execute(
        select(GapAnalysis)
        .where(
            GapAnalysis.job_analysis_id == job_id,
            GapAnalysis.deleted_at.is_(None),
        )
        .order_by(GapAnalysis.created_at.desc())
        .limit(1)
    )
    gap_analysis = gap_result.scalar_one_or_none()
    if gap_analysis is None:
        gap_response = await analyze_gaps(job_id, db, provider)
        ga_result2 = await db.execute(
            select(GapAnalysis).where(GapAnalysis.id == gap_response.id)
        )
        gap_analysis = ga_result2.scalar_one()

    cluster_ids, cluster_categories, clusters_by_id = gap_detector(gap_analysis)

    if not cluster_ids:
        state: InterviewState = _build_state(
            mode="targeted",
            job_id=job_id,
            gap_analysis_id=gap_analysis.id,
            profile_id=profile_record.id,
            critical_gaps=[],
            gap_categories={},
            gap_clusters_by_id={},
            current_question="",
            hard_ceiling=INTERVIEW_HARD_CEILING_TARGETED,
        )
        record = _make_session_record(
            job_id=job_id,
            gap_analysis_id=gap_analysis.id,
            profile_id=profile_record.id,
            mode="targeted",
            status="complete",
            state=state,
            hard_ceiling=INTERVIEW_HARD_CEILING_TARGETED,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        no_gaps_msg = "No critical gaps identified — your profile is a strong match!"
        return SessionCreateResponse(
            session_id=record.id,
            mode="targeted",
            first_question=no_gaps_msg,
            question=no_gaps_msg,
            estimated_questions=0,
            gaps_total=0,
            gaps_remaining=0,
        )

    first_cluster_id = cluster_ids[0]
    first_category = cluster_categories.get(first_cluster_id)
    state = _build_state(
        mode="targeted",
        job_id=job_id,
        gap_analysis_id=gap_analysis.id,
        profile_id=profile_record.id,
        critical_gaps=cluster_ids,
        gap_categories=cluster_categories,
        gap_clusters_by_id=clusters_by_id,
        current_question="",
        hard_ceiling=INTERVIEW_HARD_CEILING_TARGETED,
    )
    q_data = await question_generator_with_profile(
        state, profile_record.profile_json, provider, gap_category=first_category
    )
    first_question = q_data["question"]
    first_choices = q_data["choices"]
    state["current_question"] = first_question
    state["current_choices"] = first_choices
    state["messages"].append({"role": "assistant", "content": first_question})
    state["questions_asked"] = 1

    record = _make_session_record(
        job_id=job_id,
        gap_analysis_id=gap_analysis.id,
        profile_id=profile_record.id,
        mode="targeted",
        status="active",
        state=state,
        hard_ceiling=INTERVIEW_HARD_CEILING_TARGETED,
        questions_asked=1,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return SessionCreateResponse(
        session_id=record.id,
        mode="targeted",
        first_question=first_question,
        question=first_question,
        estimated_questions=_estimated_questions("targeted"),
        gaps_total=len(cluster_ids),
        gaps_remaining=len(cluster_ids),
        choices=first_choices,
    )
```

- [ ] **Step 3: Update the resumed-session path in create_session() to include choices**

In `create_session()`, find the resumed-session block and update the return:

```python
    if existing is not None:
        state: InterviewState = dict(existing.state)
        gaps_total = len(state.get("critical_gaps", []))
        gaps_remaining = gaps_total - state.get("current_gap_index", 0)
        estimated = _estimated_questions(existing.mode)
        current_q = state.get("current_question", "")
        current_choices = state.get("current_choices")
        return SessionCreateResponse(
            session_id=existing.id,
            mode=existing.mode,
            first_question=current_q,
            question=current_q,
            estimated_questions=estimated,
            gaps_total=gaps_total,
            gaps_remaining=gaps_remaining,
            choices=current_choices,
            resumed=True,
        )
```

- [ ] **Step 4: Update _create_guided_session() to use new _build_state signature**

In `_create_guided_session()`, update the `_build_state` call:

```python
    state: InterviewState = _build_state(
        mode="guided",
        job_id=job_id,
        gap_analysis_id=None,
        profile_id=profile_record.id,
        critical_gaps=sections,
        gap_categories={},
        gap_clusters_by_id={},
        current_question="",
        hard_ceiling=INTERVIEW_HARD_CEILING_GUIDED,
    )
    q_data = await question_generator_with_profile(
        state,
        profile_record.profile_json,
        provider,
        gap_category=None,
        job_context=job_context,
    )
    first_question = q_data["question"]
    state["current_question"] = first_question
    state["current_choices"] = None
    state["messages"].append({"role": "assistant", "content": first_question})
    state["questions_asked"] = 1
```

- [ ] **Step 5: Update _create_micro_session() to use cluster lookup**

Replace `_create_micro_session` with:

```python
async def _create_micro_session(
    job_id: uuid.UUID,
    job: JobAnalysis,
    profile_record: MasterProfile | None,
    target_cluster_id: str,
    db: AsyncSession,
    provider: LLMProvider,
) -> SessionCreateResponse:
    """Create a 1-question micro-session scoped to a single cluster (Gap-Click mode)."""
    if profile_record is None:
        raise LookupError(
            "No profile found — upload a CV first before using Gap-Click mode"
        )

    # Load latest gap analysis to find the cluster
    gap_result = await db.execute(
        select(GapAnalysis)
        .where(
            GapAnalysis.job_analysis_id == job_id,
            GapAnalysis.deleted_at.is_(None),
        )
        .order_by(GapAnalysis.created_at.desc())
        .limit(1)
    )
    gap_analysis = gap_result.scalar_one_or_none()

    cluster: dict = {"id": target_cluster_id, "label": target_cluster_id, "gaps": [], "jd_skills": [], "jd_context": ""}
    gap_category: str | None = None
    if gap_analysis is not None:
        clusters_raw: list[dict] = list(gap_analysis.gap_clusters or [])
        for c in clusters_raw:
            if c.get("id") == target_cluster_id:
                cluster = c
                gap_category = c.get("category")
                break

    _MICRO_CEILING = 1
    state: InterviewState = _build_state(
        mode="targeted",
        job_id=job_id,
        gap_analysis_id=gap_analysis.id if gap_analysis else None,
        profile_id=profile_record.id,
        critical_gaps=[target_cluster_id],
        gap_categories={target_cluster_id: gap_category or "C"},
        gap_clusters_by_id={target_cluster_id: cluster},
        current_question="",
        hard_ceiling=_MICRO_CEILING,
    )
    q_data = await question_generator_with_profile(
        state, profile_record.profile_json, provider, gap_category=gap_category
    )
    first_question = q_data["question"]
    first_choices = q_data["choices"]
    state["current_question"] = first_question
    state["current_choices"] = first_choices
    state["messages"].append({"role": "assistant", "content": first_question})
    state["questions_asked"] = 1

    existing_active = await _get_active_session(job_id, db)
    if existing_active is not None:
        existing_active.status = "complete"
        existing_active.updated_at = datetime.now(timezone.utc)
        await db.flush()

    record = _make_session_record(
        job_id=job_id,
        gap_analysis_id=gap_analysis.id if gap_analysis else None,
        profile_id=profile_record.id,
        mode="targeted",
        status="active",
        state=state,
        hard_ceiling=_MICRO_CEILING,
        questions_asked=1,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return SessionCreateResponse(
        session_id=record.id,
        mode="targeted",
        first_question=first_question,
        question=first_question,
        estimated_questions=1,
        gaps_total=1,
        gaps_remaining=1,
        choices=first_choices,
    )
```

- [ ] **Step 6: Update create_session() to pass target_cluster_id (not target_gap)**

In `create_session()`, update the micro-session call:

```python
    if request.target_gap and resolved_mode == "targeted":
        return await _create_micro_session(job_id, job, profile_record, request.target_gap, db, provider)
```

No change needed here — `request.target_gap` now carries the cluster ID string.

- [ ] **Step 7: Update send_message() — remove cross-gap block and propagate choices**

Replace the `send_message` function (find the section after `response_parser` call):

Replace this block:
```python
    # --- ResponseParser ---
    patch = await response_parser(
        current_gap, current_question, message, provider, remaining_gaps
    )
```

With:
```python
    clusters_by_id = state.get("gap_clusters_by_id") or {}
    current_cluster = clusters_by_id.get(current_gap, {"label": current_gap})
    cluster_label = current_cluster.get("label", current_gap)

    # --- ResponseParser ---
    patch = await response_parser(
        cluster_label, current_question, message, provider
    )
```

Remove the entire `remaining_gaps` computation block that was before it:
```python
    # Remove these lines:
    skipped_set = set(state.get("skipped_gaps", []))
    addressed_set = set(state.get("addressed_gaps", []))
    full_gaps = state.get("full_gaps") or state["critical_gaps"]
    remaining_gaps = [
        g for g in full_gaps
        if g != current_gap and g not in skipped_set and g not in addressed_set
    ]
```

Replace with just:
```python
    skipped_set = set(state.get("skipped_gaps", []))
    addressed_set = set(state.get("addressed_gaps", []))
```

Remove the entire cross-gap block:
```python
    # Remove this block entirely:
    newly_skipped: list[str] = []
    for also_gap in patch.get("gaps_also_addressed", []):
        if (
            also_gap in state["critical_gaps"]
            and also_gap != current_gap
            and also_gap not in state.get("addressed_gaps", [])
            and also_gap not in state.get("skipped_gaps", [])
        ):
            state.setdefault("skipped_gaps", []).append(also_gap)
            state.setdefault("addressed_gaps", []).append(also_gap)
            newly_skipped.append(also_gap)
```

In the advance block, update the next-question generation to thread choices:
```python
        next_q_data = await question_generator_with_profile(
            state,
            updated_profile,
            provider,
            gap_category=next_category,
            job_context=job_context,
        )
        next_question = next_q_data["question"]
        next_choices = next_q_data["choices"]
        state["current_question"] = next_question
        state["current_choices"] = next_choices
        state["messages"].append({"role": "assistant", "content": next_question})
        record.state = state
        record.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return SessionMessageResponse(
            complete=False,
            question=next_question,
            choices=next_choices,
            gaps_remaining=gaps_remaining,
            pending_conflicts=merge_conflicts if merge_conflicts else None,
        )
```

In the follow-up block, update similarly:
```python
        follow_up_data = await question_generator_with_profile(
            state,
            updated_profile,
            provider,
            gap_category=gap_category,
            follow_up_hint=follow_up_hint,
        )
        follow_up_question = follow_up_data["question"]
        state["current_question"] = follow_up_question
        state["current_choices"] = None  # follow-ups never have choices
        state["messages"].append({"role": "assistant", "content": follow_up_question})
        record.state = state
        record.updated_at = datetime.now(timezone.utc)
        await db.commit()

        gaps_remaining = _count_remaining(
            state["critical_gaps"],
            current_idx,
            set(state.get("skipped_gaps", [])),
        )

        return SessionMessageResponse(
            complete=False,
            question=follow_up_question,
            choices=None,
            gaps_remaining=gaps_remaining,
            pending_conflicts=merge_conflicts if merge_conflicts else None,
        )
```

- [ ] **Step 8: Commit**

```bash
git add backend/applire/services/session.py
git commit -m "feat: wire choices through session service, remove cross-gap resolution, micro-session uses cluster lookup"
```

---

## Task 9: Fix broken unit tests + add new tests

**Files:**
- Modify: `tests/unit/test_gap_analysis.py`
- Modify: `tests/unit/test_interview_service.py`
- Modify: `tests/unit/test_response_parser.py`
- Modify: `tests/unit/test_enrich_response_parser_review.py`

- [ ] **Step 1: Run unit tests to see all failures**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --tb=no -q 2>&1 | grep FAILED | head -30
```

- [ ] **Step 2: Fix test_gap_analysis.py — gap_detector now returns 3-tuple**

Find all occurrences of `targets, categories = gap_detector(ga)` and replace with `targets, categories, clusters_by_id = gap_detector(ga)`.

Also, since `gap_detector` now reads from `gap_clusters` (not `category_b`/`category_c` directly), update the test fixtures to set `gap_clusters` instead. Find these tests around line 354 and update:

```python
# Before:
def test_gap_detector_c_first():
    ...
    ga = GapAnalysis(...)
    ga.category_b = ["Python"]
    ga.category_c = ["LLMs"]
    targets, categories = gap_detector(ga)

# After:
def test_gap_detector_c_first():
    ...
    ga = GapAnalysis(...)
    ga.gap_clusters = [
        {"id": "cluster-llms", "label": "LLMs", "category": "C", "gaps": ["LLMs"], "jd_skills": [], "jd_context": ""},
        {"id": "cluster-python", "label": "Python", "category": "B", "gaps": ["Python"], "jd_skills": [], "jd_context": ""},
    ]
    targets, categories, clusters_by_id = gap_detector(ga)
    assert targets == ["cluster-llms", "cluster-python"]
    assert categories["cluster-llms"] == "C"
    assert categories["cluster-python"] == "B"
```

Apply same pattern to all gap_detector tests in `test_gap_analysis.py`. Read the file, identify each test, and update the fixture + assertion.

- [ ] **Step 3: Fix test_response_parser.py — gap_detector 3-tuple**

Find `targets, categories = gap_detector(ga)` around line 535 and update to:
```python
targets, categories, clusters_by_id = gap_detector(ga)
```
Update the assertion to use `assert len(targets) == ...` (cluster IDs count) and set `ga.gap_clusters` appropriately.

- [ ] **Step 4: Fix test_interview_service.py — response_parser signature + gaps_also_addressed removal**

Find all calls to `response_parser(...)` and remove the `remaining_gaps` argument (it's now the 4th positional — just `provider`):

```python
# Before:
result = await response_parser("Python", "Do you know Python?", "Yes, 5 years.", provider)
# No change needed — 4 args, no remaining_gaps

# But this call has remaining_gaps as keyword:
result = await response_parser("gap", "q", "a", provider, remaining_gaps=["other"])
# After:
result = await response_parser("gap", "q", "a", provider)
```

Remove all `assert result["gaps_also_addressed"] == [...]` assertions.

Remove the test `test_response_parser_cross_gap_populated` entirely — the feature is gone.

For `test_build_response_parser_prompt_includes_remaining_gaps` and `test_build_response_parser_prompt_no_remaining_gaps` — update to test the new 3-arg signature:

```python
def test_build_response_parser_prompt_basic():
    from applire.prompts.interview import build_response_parser_prompt
    prompt = build_response_parser_prompt("Python skills", "What is your Python level?", "5 years experience.")
    assert "Python skills" in prompt
    assert "5 years experience" in prompt
```

For `question_generator_with_profile` tests — update to assert dict return:

```python
# Before:
result = await question_generator_with_profile(...)
assert isinstance(result, str)

# After:
result = await question_generator_with_profile(...)
assert isinstance(result, dict)
assert "question" in result
assert isinstance(result["question"], str)
```

Also update state fixtures to include `gap_clusters_by_id`:
```python
state = {
    "mode": "targeted",
    "critical_gaps": ["cluster-python"],
    "gap_categories": {"cluster-python": "B"},
    "gap_clusters_by_id": {
        "cluster-python": {"id": "cluster-python", "label": "Python", "category": "B", "gaps": ["Python"], "jd_skills": [], "jd_context": ""}
    },
    "current_gap_index": 0,
    "messages": [],
    ...
}
```

- [ ] **Step 5: Fix test_enrich_response_parser_review.py — remove gaps_also_addressed from mock**

Find line 62 where the mock LLM response includes `"gaps_also_addressed": []` and remove that key from the dict.

- [ ] **Step 6: Add new test — gap_detector with empty clusters**

In `tests/unit/test_gap_clustering.py`, append:

```python
def test_gap_detector_empty_clusters():
    from applire.services.interview_graph import gap_detector
    from applire.models.gap import GapAnalysis
    from unittest.mock import MagicMock

    ga = MagicMock(spec=GapAnalysis)
    ga.gap_clusters = []
    ids, cats, by_id = gap_detector(ga)
    assert ids == []
    assert cats == {}
    assert by_id == {}


def test_gap_detector_c_before_b():
    from applire.services.interview_graph import gap_detector
    from applire.models.gap import GapAnalysis
    from unittest.mock import MagicMock

    ga = MagicMock(spec=GapAnalysis)
    ga.gap_clusters = [
        {"id": "cluster-b", "label": "B Cluster", "category": "B", "gaps": ["b1"], "jd_skills": [], "jd_context": ""},
        {"id": "cluster-c", "label": "C Cluster", "category": "C", "gaps": ["c1"], "jd_skills": [], "jd_context": ""},
    ]
    ids, cats, by_id = gap_detector(ga)
    assert ids[0] == "cluster-c"
    assert ids[1] == "cluster-b"
```

- [ ] **Step 7: Run all unit tests to verify they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --tb=short -q
```

Expected: all pass (or only pre-existing unrelated failures). Resolve any remaining failures before proceeding.

- [ ] **Step 8: Commit**

```bash
git add tests/unit/test_gap_analysis.py tests/unit/test_interview_service.py tests/unit/test_response_parser.py tests/unit/test_enrich_response_parser_review.py tests/unit/test_gap_clustering.py
git commit -m "test: fix unit tests for cluster-aware gap_detector, response_parser, question_generator"
```

---

## Task 10: Frontend i18n + GapClusterCard + gaps/page.tsx redesign

**Files:**
- Modify: `frontend/messages/de.json`
- Modify: `frontend/messages/en.json`
- Create: `frontend/components/gaps/GapClusterCard.tsx`
- Modify: `frontend/app/flow/[flowId]/gaps/page.tsx`

- [ ] **Step 1: Add new i18n keys to de.json**

In `frontend/messages/de.json`, inside the `"gaps"` object, add:

```json
"clustersToAddress": "{count, plural, one {# Thema zu adressieren} other {# Themen zu adressieren}}",
"clusterCardAnswerButton": "Beantworten",
"clusterCardConstituentLabel": "Umfasst:",
"clusterCardJdContext": "Warum relevant:",
"clusterStatusOpen": "Offen",
"clusterStatusResolved": "Beantwortet",
"clusterCategoryC": "Nicht nachgewiesen",
"clusterCategoryB": "Wahrscheinlich vorhanden",
"choiceCardHint": "Wähle einen Startpunkt (editierbar):"
```

- [ ] **Step 2: Add new i18n keys to en.json**

In `frontend/messages/en.json`, inside the `"gaps"` object, add:

```json
"clustersToAddress": "{count, plural, one {# topic to address} other {# topics to address}}",
"clusterCardAnswerButton": "Answer",
"clusterCardConstituentLabel": "Covers:",
"clusterCardJdContext": "Why relevant:",
"clusterStatusOpen": "Open",
"clusterStatusResolved": "Answered",
"clusterCategoryC": "No evidence found",
"clusterCategoryB": "Likely present",
"choiceCardHint": "Pick a starting point (editable):"
```

- [ ] **Step 3: Create GapClusterCard component**

```tsx
// frontend/components/gaps/GapClusterCard.tsx
"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

export interface GapCluster {
  id: string;
  label: string;
  category: "B" | "C";
  gaps: string[];
  jd_skills: string[];
  jd_context: string;
}

interface GapClusterCardProps {
  cluster: GapCluster;
  resolved: boolean;
  onAnswer: () => void;
  children?: React.ReactNode; // GapClickPanel injected by parent
}

export function GapClusterCard({
  cluster,
  resolved,
  onAnswer,
  children,
}: GapClusterCardProps) {
  const t = useTranslations("gaps");

  const borderColor = resolved
    ? "border-l-green-500"
    : cluster.category === "C"
      ? "border-l-red-500"
      : "border-l-yellow-400";

  const dotColor = resolved
    ? "bg-green-500"
    : cluster.category === "C"
      ? "bg-red-500"
      : "bg-yellow-400";

  return (
    <div
      className={cn(
        "rounded-lg border border-gray-200 bg-white shadow-sm border-l-4 p-4",
        borderColor,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2 min-w-0">
          <span
            className={cn("mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full", dotColor)}
          />
          <div className="min-w-0">
            <p className="font-semibold text-neutral-dark text-sm">{cluster.label}</p>
            {cluster.jd_context && (
              <p className="text-xs text-gray-500 mt-0.5">{cluster.jd_context}</p>
            )}
            {cluster.gaps.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                <span className="text-xs text-gray-400">{t("clusterCardConstituentLabel")}</span>
                {cluster.gaps.map((g) => (
                  <span
                    key={g}
                    className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                  >
                    {g}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
        {!resolved && (
          <button
            className="shrink-0 rounded-md bg-teal px-3 py-1.5 text-xs font-medium text-white hover:bg-teal/90 transition-colors"
            onClick={onAnswer}
          >
            {t("clusterCardAnswerButton")}
          </button>
        )}
        {resolved && (
          <span className="shrink-0 text-xs font-medium text-green-600">
            ✓ {t("clusterStatusResolved")}
          </span>
        )}
      </div>
      {children}
    </div>
  );
}
```

- [ ] **Step 4: Rewrite gaps/page.tsx**

The key changes to `frontend/app/flow/[flowId]/gaps/page.tsx`:

**4a. Add `GapCluster` type and update `GapAnalysis` interface:**

```tsx
interface GapCluster {
  id: string;
  label: string;
  category: "B" | "C";
  gaps: string[];
  jd_skills: string[];
  jd_context: string;
}

interface GapAnalysis {
  id: string;
  match_score: number;
  category_a: string[];
  category_b: string[];
  category_c: string[];
  strengths: string[];
  gap_clusters: GapCluster[];
}
```

**4b. Update `GapClickState` to include choices:**

```tsx
interface GapClickState {
  status: GapStatus;
  sessionId: string | null;
  question: string | null;
  choices: string[] | null;
  answer: string;
  sending: boolean;
  error: string;
}

const EMPTY_GAP_STATE: GapClickState = {
  status: "idle",
  sessionId: null,
  question: null,
  choices: null,
  answer: "",
  sending: false,
  error: "",
};
```

**4c. Update `startMicroSession` in `GapClickPanel` to read `choices` from response and pass cluster ID:**

```tsx
async function startMicroSession() {
  onUpdate({ status: "loading", error: "" });
  try {
    const res = await fetch(`${API_BASE}/api/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId, mode: "targeted", target_gap: clusterId }),
    });
    if (!res.ok) throw new Error(await apiErrorMessage(res));
    const data = await res.json();
    onUpdate({
      status: "question",
      sessionId: data.session_id,
      question: data.question ?? data.first_question,
      choices: data.choices ?? null,
    });
  } catch (e: unknown) {
    onUpdate({ status: "idle", error: e instanceof Error ? e.message : "Failed to start" });
  }
}
```

Update `GapClickPanel` props to accept `clusterId: string` instead of `gap: string`.

**4d. Add choice cards inside GapClickPanel (when in `question` or `answering` status):**

```tsx
{state.choices && state.choices.length > 0 && (
  <div className="space-y-1.5">
    <p className="text-xs text-gray-400">{t("choiceCardHint")}</p>
    <div className="flex flex-col gap-1">
      {state.choices.map((choice) => (
        <button
          key={choice}
          type="button"
          className={cn(
            "w-full text-left rounded border border-teal/30 px-3 py-2 text-xs text-neutral-dark",
            "hover:bg-teal/5 transition-colors",
            state.answer === choice ? "bg-teal/10 border-teal/60 font-medium" : "bg-white",
          )}
          onClick={() => onUpdate({ answer: choice, status: "answering" })}
        >
          {choice}
        </button>
      ))}
    </div>
  </div>
)}
```

**4e. Replace the category B/C list rendering in the main page body with cluster cards:**

Replace the section that maps `gaps.category_c` and `gaps.category_b` as list items with:

```tsx
{/* Cluster-based gap display */}
{gaps.gap_clusters.length > 0 ? (
  <div className="space-y-3">
    <div className="flex items-center justify-between">
      <h3 className="font-semibold text-neutral-dark text-sm">
        {t("clustersToAddress", {
          count: gaps.gap_clusters.filter(
            (c) => gapStates[c.id]?.status !== "resolved"
          ).length,
        })}
      </h3>
    </div>
    {gaps.gap_clusters
      .sort((a, b) => {
        if (a.category === "C" && b.category !== "C") return -1;
        if (a.category !== "C" && b.category === "C") return 1;
        return 0;
      })
      .map((cluster) => {
        const gapState = gapStates[cluster.id] ?? EMPTY_GAP_STATE;
        const isResolved = gapState.status === "resolved";
        return (
          <GapClusterCard
            key={cluster.id}
            cluster={cluster}
            resolved={isResolved}
            onAnswer={() =>
              updateGapState(cluster.id, { status: "loading" })
            }
          >
            {!isResolved && (
              <GapClickPanel
                clusterId={cluster.id}
                jobId={gaps_jobId}
                state={gapState}
                onUpdate={(patch) => updateGapState(cluster.id, patch)}
                onResolved={() => {
                  updateGapState(cluster.id, { status: "resolved" });
                  void refetchGaps();
                }}
              />
            )}
          </GapClusterCard>
        );
      })}
  </div>
) : (
  /* Fallback: no clusters (gap analysis not yet run or old record) */
  <p className="text-sm text-gray-500">{t("analyzing")}</p>
)}
```

Note: `gapStates` keying changes from gap strings to cluster IDs. Also add `updateGapState` helper:
```tsx
function updateGapState(clusterId: string, patch: Partial<GapClickState>) {
  setGapStates((prev) => ({
    ...prev,
    [clusterId]: { ...(prev[clusterId] ?? EMPTY_GAP_STATE), ...patch },
  }));
}
```

- [ ] **Step 5: Start dev server and verify gaps page loads and shows cluster cards**

```bash
cd frontend && npm run dev
```

Open `http://localhost:3000` and navigate to the gaps page. Verify:
- Cluster cards render with left-border color coding (red = C, yellow = B)
- Constituent gap chips appear
- "Beantworten" button triggers micro-session
- After answering, card shows green "✓ Beantwortet"

- [ ] **Step 6: Commit**

```bash
git add frontend/messages/de.json frontend/messages/en.json frontend/components/gaps/GapClusterCard.tsx frontend/app/flow/[flowId]/gaps/page.tsx
git commit -m "feat: redesign gaps page with cluster cards, JD context, and choice cards in GapClickPanel"
```

---

## Task 11: Interview page split-screen redesign

**Files:**
- Modify: `frontend/app/flow/[flowId]/interview/page.tsx`

Changes: 65/35 split layout; right panel with cluster tracker and match score gauge; left panel adds choice cards; replace `requiredSkills` sidebar with cluster tracker.

- [ ] **Step 1: Add GapCluster type and fetch to interview page**

At the top of the file, add the `GapCluster` interface (same as gaps page):

```tsx
interface GapCluster {
  id: string;
  label: string;
  category: "B" | "C";
  gaps: string[];
  jd_skills: string[];
  jd_context: string;
}

interface GapAnalysisData {
  id: string;
  match_score: number;
  gap_clusters: GapCluster[];
}
```

Update `SessionCreateResponse` and `MessageResponse` types to include `choices`:

```tsx
interface SessionCreateResponse {
  session_id: string;
  mode: "targeted" | "guided";
  first_question: string;
  question: string;
  estimated_questions: number;
  gaps_total: number;
  gaps_remaining: number;
  choices: string[] | null;
  resumed: boolean;
}

interface MessageResponse {
  complete: boolean;
  question?: string;
  gaps_remaining?: number;
  choices?: string[] | null;
  reason?: "gaps_resolved" | "user_ended" | "max_questions_reached";
  questions_asked?: number;
  gaps_resolved?: number;
  completeness_score?: number;
  pending_conflicts?: ConflictSummary[];
}
```

Add state variables for clusters, current choices, and cluster resolution tracking:

```tsx
const [gapAnalysis, setGapAnalysis] = useState<GapAnalysisData | null>(null);
const [resolvedClusterIds, setResolvedClusterIds] = useState<Set<string>>(new Set());
const [currentClusterId, setCurrentClusterId] = useState<string | null>(null);
const [choices, setChoices] = useState<string[] | null>(null);
```

Add a fetch for gap analysis on mount (after flow state is loaded):

```tsx
// Inside the useEffect that loads flow state, after getting job_id:
if (jobId) {
  fetch(`${API_BASE}/api/job/${jobId}/gaps`)
    .then((r) => r.ok ? r.json() : null)
    .then((data) => {
      if (data) setGapAnalysis(data);
    })
    .catch(() => {});
}
```

- [ ] **Step 2: Update session creation to capture choices and first cluster ID**

When `POST /api/session` returns, extract choices and current cluster:

```tsx
setChoices(data.choices ?? null);
// Try to match first gap_cluster from analysis
if (gapAnalysis && gapAnalysis.gap_clusters.length > 0) {
  setCurrentClusterId(gapAnalysis.gap_clusters[0].id);
}
```

When a message response returns with a new question, update choices and advance cluster:

```tsx
setChoices(resp.choices ?? null);
// Advance to next cluster if gaps_remaining decreased
if (gapAnalysis && resp.gaps_remaining !== undefined) {
  const totalClusters = gapAnalysis.gap_clusters.length;
  const nextIdx = totalClusters - (resp.gaps_remaining ?? 0);
  const nextCluster = gapAnalysis.gap_clusters[nextIdx];
  if (nextCluster) setCurrentClusterId(nextCluster.id);
  // Mark previous cluster resolved
  if (currentClusterId) {
    setResolvedClusterIds((prev) => new Set([...prev, currentClusterId]));
  }
}
```

- [ ] **Step 3: Rewrite the main layout to split-screen 65/35**

Replace the top-level return JSX with:

```tsx
return (
  <div className="min-h-screen bg-gray-50">
    {/* Mobile sticky header */}
    <div className="md:hidden sticky top-0 z-10 bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
      <span className="text-xs font-medium text-neutral-dark truncate max-w-[60%]">
        {currentClusterId
          ? gapAnalysis?.gap_clusters.find((c) => c.id === currentClusterId)?.label
          : t("loading")}
      </span>
      {matchScore !== null && (
        <span className="text-xs font-semibold text-teal">{Math.round(matchScore * 100)}%</span>
      )}
    </div>

    <div className="flex flex-col md:flex-row md:h-screen">
      {/* LEFT PANEL — 65% */}
      <div className="flex-1 md:w-[65%] overflow-y-auto p-4 md:p-8">
        {/* Progress */}
        {sessionData && !completion && (
          <div className="mb-6">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>
                {t("questionOf", {
                  current: messages.filter((m) => m.role === "assistant").length,
                  total: sessionData.estimated_questions,
                })}
              </span>
              <span className="font-medium text-neutral-dark">
                {currentClusterId
                  ? gapAnalysis?.gap_clusters.find((c) => c.id === currentClusterId)?.label
                  : ""}
              </span>
            </div>
            {sessionData.gaps_total > 0 && (
              <ProgressLinear
                value={Math.round(
                  ((sessionData.gaps_total - (sessionData.gaps_remaining ?? 0)) /
                    sessionData.gaps_total) *
                    100
                )}
              />
            )}
          </div>
        )}

        {/* Question + conversation */}
        {/* ... existing message list rendering ... */}

        {/* Choice cards */}
        {choices && choices.length > 0 && !completion && (
          <div className="mt-4 space-y-2">
            <p className="text-xs text-gray-400">{t("choiceCardHint")}</p>
            {choices.map((choice) => (
              <button
                key={choice}
                type="button"
                className={cn(
                  "w-full text-left rounded-lg border px-4 py-3 text-sm transition-colors",
                  input === choice
                    ? "border-teal bg-teal/5 font-medium text-neutral-dark"
                    : "border-gray-200 bg-white text-gray-700 hover:border-teal/50 hover:bg-gray-50"
                )}
                onClick={() => setInput(choice)}
              >
                {choice}
              </button>
            ))}
          </div>
        )}

        {/* Textarea + Submit */}
        {/* ... existing textarea and send button ... */}
      </div>

      {/* RIGHT PANEL — 35% (hidden on mobile, accessible via collapsed details) */}
      <aside className="hidden md:flex md:w-[35%] flex-col border-l border-gray-200 bg-white overflow-y-auto p-6">
        {/* Match score gauge */}
        {matchScore !== null && <CompletenessGauge score={matchScore} />}

        {/* Cluster tracker */}
        {gapAnalysis && gapAnalysis.gap_clusters.length > 0 && (
          <div className="mt-6 space-y-2">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
              {t("roleRequirements")}
            </p>
            {gapAnalysis.gap_clusters.map((cluster) => {
              const isResolved = resolvedClusterIds.has(cluster.id);
              const isCurrent = cluster.id === currentClusterId;
              return (
                <div
                  key={cluster.id}
                  className={cn(
                    "rounded-md px-3 py-2 text-xs border-l-2 transition-colors",
                    isResolved
                      ? "border-l-green-500 bg-green-50 text-gray-500"
                      : isCurrent
                        ? "border-l-teal bg-teal/5 text-neutral-dark font-medium"
                        : "border-l-gray-200 text-gray-400"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span>
                      {isResolved ? "✓" : isCurrent ? "►" : "○"}
                    </span>
                    <span className="truncate">{cluster.label}</span>
                  </div>
                  {cluster.jd_skills.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1 ml-5">
                      {cluster.jd_skills.slice(0, 3).map((skill) => (
                        <span
                          key={skill}
                          className="rounded-full bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Mobile collapsed tracker */}
        <details className="md:hidden mt-4">
          <summary className="text-xs font-medium text-gray-500 cursor-pointer">
            ▸ {t("roleRequirements")}
          </summary>
          {/* same cluster list as above */}
        </details>
      </aside>
    </div>
  </div>
);
```

Note: Keep all existing state variables (`input`, `messages`, `sessionData`, `completion`, `conflicts`, etc.) and all existing logic (conflict cards, completion screen, "Ich bin fertig" flow) — only the layout shell and additions change.

Add `matchScore` state extracted from the initial session create response or from `gapAnalysis.match_score`:

```tsx
const [matchScore, setMatchScore] = useState<number | null>(null);
// After session create:
setMatchScore(gapAnalysis?.match_score ?? null);
// After message response with completeness_score:
if (resp.completeness_score !== undefined) setMatchScore(resp.completeness_score);
```

Add `t("choiceCardHint")` i18n key to `frontend/messages/de.json` and `en.json` inside the `"interview"` namespace:

```json
"choiceCardHint": "Wähle einen Startpunkt (editierbar):"
```
```json
"choiceCardHint": "Pick a starting point (editable):"
```

- [ ] **Step 4: Test split-screen layout in dev server**

Verify:
- Desktop (≥768px): 65% left panel + 35% right panel side by side
- Mobile (<768px): single column, sticky header pill with cluster label + match %, full-width interview
- Right panel shows cluster tracker with ✓ / ► / ○ icons
- Choice cards appear in left panel when API returns choices
- Clicking a choice pre-fills the textarea
- Existing interview flow (send, conflict cards, completion screen) still works

- [ ] **Step 5: Run frontend type check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: 0 errors

- [ ] **Step 6: Commit**

```bash
git add frontend/app/flow/[flowId]/interview/page.tsx frontend/messages/de.json frontend/messages/en.json
git commit -m "feat: split-screen interview page with cluster tracker right panel and choice cards"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Gap Clustering — Task 3 (prompt) + Task 4 (service + _run_analysis)
- [x] JD Context — stored in GapCluster.jd_context, displayed in GapClusterCard and GapClickPanel
- [x] Multiple Choice Questions — Tasks 6–8 (prompt → dict return → schema → session → frontend)
- [x] Split-screen layout — Task 11
- [x] GapClusterCard — Task 10
- [x] GapClickPanel choice cards — Task 10
- [x] Cluster tracker right panel — Task 11
- [x] Mobile layout — Task 11 (flex-col on mobile, sticky header, collapsed tracker)
- [x] gap_clusters JSONB column + migration — Task 1
- [x] GapClusterSchema Pydantic — Task 2
- [x] gap_detector returns 3-tuple — Task 7
- [x] response_parser drops gaps_also_addressed — Tasks 6 + 7
- [x] Existing unit tests fixed — Task 9
- [x] No backwards compatibility — no fallback for old records (spec requirement met)

**Type consistency check:**
- `GapClusterSchema` defined in `schemas/gap_cluster.py` — used in Tasks 2, 4
- `gap_detector()` returns `tuple[list[str], dict[str, str], dict]` — consumed in Task 8
- `question_generator_with_profile()` returns `dict` (`{"question": str, "choices": list[str] | None}`) — consumed in Task 8
- `response_parser(cluster_label, question, answer, provider)` — 4 args, no remaining_gaps — matches Task 6 and 7
- `build_question_prompt(cluster: dict, ...)` — matches Task 6 definition and Task 7 usage
- `build_response_parser_prompt(cluster_label, question, answer)` — 3 args — matches Task 6 definition and Task 7 usage
- `_build_state(gap_clusters_by_id=...)` — new kwarg — matches Task 8 all call sites
- Frontend `GapCluster` interface mirrors backend `GapClusterSchema` — both defined in Tasks 2 and 10
