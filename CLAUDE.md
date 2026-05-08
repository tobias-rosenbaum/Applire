# Applire — Claude Code Guide

## Project Overview

**Applire** is an AI-powered DACH CV tailoring platform built as an open-core product.
- **License**: AGPL-3.0 (Community Edition)
- **Founder**: Tobias Rosenbaum
- **Architecture doc**: `Documents/Architecture/arc42.md` (authoritative)
- **ADRs**: `Documents/Architecture/ADR.md`
- **Sprint specs**: `Documents/Sprints/sprint N.md`

---
## Ways of working
This project operates in sprints. The user will ask you to create a new sprint and tell you the scope of the implementation. You check the relevant Documentation and use the superpowers skill for the individual step.

### Branching and merging
Create a branch for each new sprint. Check that the sprints from previous sprints have been successfully merged into main. After the implementation is finished and the user conducted user acceptance testing, push to the repo and create a pull request.

### User Journeys, Epics and User Stories.
Check the user journeys in `Documents/Product Specifications/Personas` on whether the sprint impacts any of the existing journeys or whether additional journeys are needed. Next, if journeys are impacted, update the `Documents/Product Specifications/Epic_and_User_Story_Tracker.csv`. Reference these in the plan you write later.

### Architecture and Decisions
Check the architecture Documentation in `Documents/Architecture/`. If major decisions are made as part of a sprint, propose to document the decision as an ADR entry and update the arc42.md document if necessary. Both documents should be up to date so that future agents get a comprehensive and accurate set of information about the project




## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL 16 |
| LLM (default) | Mistral AI (EU-native) — via LLM Provider Abstraction |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS v4, ShadCN/Radix UI |
| PDF Engine | Jinja2 templates → Playwright headless Chromium |
| MCP Server | Python `mcp` SDK (`FastMCP`), stdio (Community), SSE (Cloud) |
| Infrastructure | Docker Compose, Hetzner Cloud (DE) |
| Testing | pytest, Vitest, Playwright |

---

## Key Directories

```
Solution/
├── backend/
│   ├── applire/             # Core Python package (AGPL-3.0)
│   │   ├── routers/        # FastAPI route handlers
│   │   ├── services/       # Business logic (interview/, flow/, etc.)
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── retention/      # GDPR retention worker
│   │   └── constants.py    # Thresholds and config constants
│   ├── alembic/            # DB migrations
│   └── tests/              # In-container CI variant (connects to backend:8000)
├── frontend/
│   ├── app/                # Next.js app router pages
│   ├── components/         # React components
│   └── lib/                # Shared utilities
├── tests/
│   ├── unit/               # Fast, no Docker (sys.path includes backend/)
│   ├── integration/        # Full-stack LLM tests (INTEGRATION_LLM=1)
│   ├── e2e/                # Playwright TypeScript tests
│   ├── fixtures/           # Sample CVs, JDs, downloads
│   └── test_iter*.py       # Per-iteration API tests (Docker stack)
├── Documents/              # Project docs (specs, sprints, arch) — NOT in git index
├── docker-compose.yml      # Full stack
└── playwright.config.ts    # E2E config (Chromium + Firefox)
```

---

## Build & Run Commands

```bash
# Full stack (backend + frontend + postgres + retention worker)
docker-compose up -d

# Frontend dev (standalone)
cd frontend && npm run dev           # http://localhost:3000

# Backend (standalone, requires DB)
cd backend && uvicorn applire.main:app --reload --port 8001

# DB migrations
cd backend && alembic upgrade head

# Frontend unit tests (Vitest — no Docker)
cd frontend && npm test

# Backend unit tests (no Docker)
cd Solution && pytest tests/unit/ -v --cov=applire --cov-report=html

# Backend integration tests (spins up Docker stack)
cd Solution && pytest tests/test_iter*.py -v

# Full happy-path LLM test (real API key required)
INTEGRATION_LLM=1 pytest tests/integration/test_happy_path.py -v

# E2E tests (requires running app)
cd Solution && npx playwright test
npx playwright test --headed          # Headed mode for debugging
npx playwright show-report            # View HTML report
```

---

## Architecture Rules

### Core Patterns
- **Stateful Backend**: Complex reasoning (Interview Orchestrator, Flow Orchestrator) stays server-side; frontend is thin
- **Provider Abstraction**: Auth, LLM, Storage, OCR all use factory/interface pattern — pluggable for self-hosters
- **MCP Agent-First**: All user-facing functionality must be accessible as MCP tools; Kaile is a channel, not a persona

### Flow Orchestrator State Machine
Linear DAG: `jd_analysis → cv_import → gap_analysis → interview → cv_generation → complete`
- One `flow_session` per `(user_id, job_id)`; `flow_id` is stable handle for agent recovery
- Steps requiring artifacts must pass `artifact_id` in `AdvanceFlowRequest` (HTTP 422 if missing)

### GDPR & Data Retention
- Retention Worker runs daily (`applire/retention/worker.py`)
- TTLs: uploads 7d, interview_sessions 30d, generated_cvs 90d/24h (human/agent), master_profiles 730d inactivity
- 100% EU data residency — no US sub-processors

### CV Preview
- Frontend fetches `GET /api/cv/{id}/html` via `fetch()`, injects into `<iframe srcDoc=…>`
- Never use `<iframe src=…>` for CV preview — cross-origin framing blocked by Firefox CSP

---

## Testing Rules

| Tier | When | Blocking? |
|---|---|---|
| Unit tests | Pre-commit (advisory) | No |
| CI unit + integration + E2E | Post-commit (GitHub Actions) | **Yes** |
| Manual QA | Pre-rollout | **Yes** — no deploy without passing |

- **Coverage gate**: ≥75% backend unit coverage (`pytest --cov-fail-under=75`)
- **All CI tests mock LLM providers** — never call real Mistral/OpenAI in CI
- Unit tests run without Docker (`tests/unit/conftest.py` overrides Docker fixture)
- Integration tests (`tests/test_iter*.py`) spin up the Docker stack automatically via `conftest.py`
- E2E tests run against Chromium AND Firefox projects

---

## Documentation Rules

- **`Documents/`** — internal Applire docs (architecture, sprints, ADRs). Synced to Nextcloud; **not** part of the git repo. Never commit files from here.
- **`docs/`** — repo-specific documentation (TESTING.md, plans, tech-debt notes, etc.). This IS part of the repository and should be committed normally.
- Do not delete files in either folder unless the user explicitly asks.
- Architecture changes that warrant an ADR → add to `Documents/Architecture/ADR.md` and reference in `arc42.md` (Nextcloud only — do not commit).

---

## Key Files

| File | Purpose |
|---|---|
| `backend/applire/constants.py` | Interview thresholds, TTLs, edition flags |
| `backend/applire/services/flow/orchestrator.py` | Flow state machine (`VALID_TRANSITIONS`) |
| `backend/applire/services/interview/signals.py` | Done-signal detection (deterministic, no LLM) |
| `backend/applire/routers/cv.py` | CV HTML + PDF endpoints |
| `frontend/components/cv/CVPreview.tsx` | CV preview (srcDoc pattern) |
| `Documents/Architecture/arc42.md` | Authoritative architecture document |
| `Documents/Sprints/sprint N.md` | Sprint specs and acceptance criteria |

---

## Conventions

- Python: Black formatting, type annotations on all new code
- TypeScript: strict mode, no `any`
- Database: all schema changes via Alembic migrations — never raw DDL
- MCP tools: always async, short-lived `AsyncSession` per tool call
- Git: conventional commits (`feat:`, `fix:`, `test:`, `chore:`, `docs:`)
- Never skip `--no-verify` or bypass CI gates
- **Branch per sprint**: always create and work on a dedicated branch named `sprint-N` (e.g. `sprint-16`) at the start of each sprint. Never commit sprint work directly to `main`. Merge (or PR) to `main` only when the sprint is complete and all tests pass.
