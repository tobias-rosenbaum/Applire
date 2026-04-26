# Gap-View Redesign — Design Spec

**Date:** 2026-04-22  
**Sprint:** TBD  
**Status:** Approved

## Problem Statement

The current Gap-View displays every individual gap as a separate list item. A test run against an AI automation role produced 50 displayed gaps — factually ~8–10 unique topics, inflated by semantically redundant entries (e.g. "Agentic Systems", "Agentic Orchestration", "AI Systems", "LLMs" appearing as four separate items). This overwhelms users before the interview even starts.

Four improvements are in scope:

1. **Gap Clustering** — proactive semantic grouping at analysis time
2. **JD Context** — show why each cluster is relevant to the role
3. **Multiple Choice Questions** — reduce free-text burden for broad/confirmatory gaps
4. **Redesigned Layout** — split-screen interview UI modelled on provided design mockups

## Decision: Approach A (Two-Phase Gap Analysis)

The existing gap analysis prompt (`prompts/gap_analysis.py`) is left unchanged. A second, lightweight LLM step runs immediately after and groups the B+C gaps into semantic clusters. Clusters are stored in a new `gap_clusters` JSONB column on `GapAnalysis`. No backwards compatibility or fallback for old records is required.

---

## Section 1: Data Model

### New column: `gap_analyses.gap_clusters`

Type: `JSONB NOT NULL DEFAULT '[]'`  
Migration: new Alembic revision (e.g. `0028_gap_clusters.py`)

Each element in the array is a **GapCluster** object:

```json
{
  "id": "cluster-agentic",
  "label": "Agentic AI Systems",
  "category": "C",
  "gaps": ["Agentic Systems", "Agentic Orchestration", "AI Systems", "LLMs"],
  "jd_skills": ["LLM-based Agent Design", "Multi-Agent Orchestration"],
  "jd_context": "Die Stelle sucht jemanden, der autonome KI-Agenten designt und orchestriert — nicht nur Tools nutzt."
}
```

| Field | Type | Description |
|---|---|---|
| `id` | string | Stable slug, e.g. `cluster-<label-kebab>` |
| `label` | string | Human-readable cluster name (LLM-generated) |
| `category` | `"B" \| "C"` | Worst category among constituent gaps (C trumps B) |
| `gaps` | string[] | Original gap strings absorbed into this cluster |
| `jd_skills` | string[] | Matching entries from `required_skills` / `nice_to_have_skills` |
| `jd_context` | string | LLM-generated sentence explaining why the role needs this cluster |

The existing `category_a`, `category_b`, `category_c` columns are unchanged.

### Updated schema: `GapAnalysisResponse`

Add `gap_clusters: list[GapClusterSchema]` field. `GapClusterSchema` is a new Pydantic model mirroring the JSON structure above.

---

## Section 2: Backend — Clustering Service

### New prompt: `prompts/gap_clustering.py`

A focused, single-purpose prompt. Input: `category_b`, `category_c` gap lists + `required_skills` + `nice_to_have_skills` from `JobAnalysis`. Output: array of `GapCluster` objects.

Guidelines embedded in the prompt:
- Merge gaps that share the same semantic domain (not just keywords)
- `category` of cluster = worst-case of members (C if any member is C)
- `jd_skills`: pick only the required/nice-to-have skills that directly motivate this cluster
- `jd_context`: one sentence, first-person role perspective, written in the language of the JD (German/English)
- Target: 5–12 clusters; never more than the number of input gaps

### New function: `cluster_gaps()` in `services/gap.py`

```python
async def cluster_gaps(
    gap_analysis: GapAnalysis,
    job_analysis: JobAnalysis,
    provider: LLMProvider,
    db: AsyncSession,
) -> None:
    """Run clustering LLM call and persist result to gap_analysis.gap_clusters."""
```

Called directly after `analyze_gaps()` completes. Writes result to `gap_analysis.gap_clusters` and commits.

### Integration points

- `POST /api/job/{job_id}/gaps` — calls `analyze_gaps()` then `cluster_gaps()`
- `POST /api/job/{job_id}/gaps/refresh` — same sequence
- `GET /api/job/{job_id}/gaps` — returns existing record including `gap_clusters`

No new API endpoints required.

### Interview graph changes: `services/interview_graph.py`

`gap_detector()` is updated to consume `gap_clusters` instead of the flat `category_c` / `category_b` lists. It returns `(ordered_clusters, cluster_map)` where `cluster_map` maps `cluster.id → GapCluster`. Category C clusters are ordered first, then B.

The `response_parser()` resolves at cluster level: when `gap_resolution != "none"`, the entire cluster is marked resolved (all constituent gaps are implicitly closed). The existing `gaps_also_addressed` field is removed from the prompt and schema — clusters make it redundant.

---

## Section 3: Multiple-Choice Questions

### Structured question output

`question_generator_with_profile()` now returns a dict instead of a plain string:

```python
{
    "question": str,
    "choices": list[str] | None  # None = text-only question
}
```

The `QUESTION_SYSTEM_PROMPT` is extended with instructions to generate 2–3 choices when:
- The cluster has ≥ 2 constituent gaps, **or**
- The cluster category is B (confirmation question)

Choices are short, specific options the candidate can select as a starting point. They are not exhaustive — the textarea remains available for custom answers.

### API changes

`POST /api/session` response adds:
```json
{ "question": "...", "choices": ["Option A", "Option B"] }
```

`POST /api/session/{id}/message` response adds:
```json
{ "question": "...", "choices": [...] | null, "complete": false, ... }
```

Old API shape (`question: string`) is extended, not replaced — no breaking change for existing consumers.

### Selection mechanic

Clicking a choice pre-fills the textarea with the choice text (editable). Multiple selection is not supported. The user can also ignore choices and type freely.

---

## Section 4: Frontend — Gaps Page

### Cluster cards replace gap list items

Each cluster renders as a card:

- **Status indicator** (left border / dot): red = Category C open, yellow = B open, green = resolved
- **Label** as card heading
- **JD context sentence** below label
- **Constituent gaps** as small chip tags ("Umfasst: …")
- **"Beantworten" button** opens the inline `GapClickPanel`

Counter in section header reads: *"8 Themen zu adressieren"* (not "50 Gaps").

### GapClickPanel extensions

1. **JD Context box** at top — shows `cluster.jd_context` + `cluster.jd_skills` as tags
2. **Choice cards** between question and textarea — clicking pre-fills textarea
3. On resolve: all constituent gaps removed from active counters; match-score refresh as before

### Component structure

- `GapClusterCard` — new component wrapping the card UI
- `GapClickPanel` — extended (JD context box + choice cards added)
- `gaps/page.tsx` — iterates over `gap_clusters` instead of `category_b / category_c`

No fallback for old records. No backwards-compatibility code.

---

## Section 5: Frontend — Interview Page (Split Screen)

### Layout: 65% / 35%, stacks on mobile

```
Desktop:
┌─────────────────────────────────┬──────────────────┐
│  LEFT PANEL (65%)               │  RIGHT PANEL(35%)│
│  Progress bar + cluster label   │  Match Score     │
│  AI avatar + question headline  │  Cluster tracker │
│  Choice cards (if any)          │  ✓ resolved      │
│  Textarea + Submit              │  ► current       │
│  "Ich bin fertig" link          │  ○ pending       │
└─────────────────────────────────┴──────────────────┘

Mobile (< 768px):
┌──────────────────────────┐
│ [Cluster label]     78%  │  ← sticky header pill
├──────────────────────────┤
│  Full-width interview    │
│  Choice cards (stacked)  │
│  Textarea + Submit       │
│  ▸ Alle Anforderungen    │  ← collapsed JD tracker
└──────────────────────────┘
```

### Left panel

- Progress: `Thema X von N` + linear progress bar
- Question displayed as large Manrope headline
- Choice cards: full-width clickable cards with icon + title + short description; clicking pre-fills textarea
- Textarea + Send button (Enter = submit, Shift+Enter = newline)
- "Ich bin fertig" confirmation flow unchanged

### Right panel

- **Match Score Gauge**: animated SVG circle (reuse existing `ScoreCircle` or new `MatchGauge`)
- **Cluster list**: all clusters with status icons (✓ / ► / ○), label, and `jd_skills` chip tags
- Active cluster highlighted with left-border accent and subtle background
- Loaded once at session start from the `gap_clusters` data; no additional API calls

### Data flow

The interview page fetches two things on mount: (1) the flow state (`GET /api/flow/{flowId}/state`) to get `job_id` and role title, (2) the gap analysis (`GET /api/job/{job_id}/gaps`) to get `gap_clusters` for the right-panel tracker. Session creation (`POST /api/session`) happens as today. Cluster statuses are tracked in local React state, updated as responses come back from `POST /api/session/{id}/message`.

The existing `requiredSkills` sidebar is removed and replaced by the cluster tracker.

---

## Out of Scope

- Voice input (shown in mockup but not requested)
- Dark mode adaptations
- MCP tool updates (separate sprint)
- Backwards compatibility for pre-clustering gap records
