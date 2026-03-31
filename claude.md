# CLAUDE.md — Apliqa Solution

## Project Overview

Apliqa is an open-source, AI-powered CV tailoring tool for the DACH job market (Community Edition). It guides job seekers through a structured flow: upload CV(s) + provide a job description → gap analysis → interview → tailored CV generation.

## Documentation

All product, architecture, and sprint documentation lives **outside** this repository:

| Document | Path |
|----------|------|
| Architecture (arc42) | `/home/kvmadmin/Dokumente/Apliqa/Documents/Architecture/arc42.md` |
| Architecture Decision Records | `/home/kvmadmin/Dokumente/Apliqa/Documents/Architecture/ADR.md` |
| User Stories & Epics | `/home/kvmadmin/Dokumente/Apliqa/Documents/Product Specifications/Epic_and_User_Story_Tracker.csv` |
| Personas | `/home/kvmadmin/Dokumente/Apliqa/Documents/Product Specifications/Personas/` |
| Sprint plans | `/home/kvmadmin/Dokumente/Apliqa/Documents/Sprints/sprint N.md` |
| Agent guidance | `/home/kvmadmin/Dokumente/Apliqa/Documents/AGENTS.md` |

**Rules:**
- Do not create documentation files inside the Solution folder — use the Documents folder instead.
- Do not delete files in the Documents folder unless explicitly asked.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (App Router), TypeScript strict, Tailwind CSS |
| Backend | Python, FastAPI, SQLAlchemy (async), Alembic |
| Database | PostgreSQL 16 (JSONB for profile storage) |
| AI / LLM | Mistral (`mistral-large-latest`) via providers abstraction |
| MCP | Custom MCP server (`python -m apliqa.mcp`) |
| Container | Docker Compose (services: `postgres`, `backend`, `frontend`, `retention`, `mcp`, `ollama`) |
| Testing | pytest (backend), Playwright (E2E) |

## Repository Structure

```
Solution/
├── backend/
│   ├── apliqa/
│   │   ├── auth/           # NoAuthProvider (Community Edition)
│   │   ├── db/             # SQLAlchemy session, models
│   │   ├── mcp/            # MCP server tools
│   │   ├── models/         # ORM models
│   │   ├── ocr/            # PDF/DOCX text extraction
│   │   ├── providers/      # LLM provider abstraction
│   │   ├── routers/        # FastAPI routers (flow, job, profile, cv, application, session)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic
│   │   ├── storage/        # File upload handling
│   │   └── main.py         # FastAPI app entry point
│   └── tests/
│       ├── integration/    # Real-LLM integration tests (gated by INTEGRATION_LLM=1)
│       └── test_iter*.py   # Per-iteration unit tests
├── frontend/
│   ├── app/
│   │   ├── page.tsx                        # Screen 1: CV Upload + JD Input
│   │   └── flow/[flowId]/
│   │       ├── processing/                 # Screen 2: Processing overlay
│   │       ├── gaps/                       # Screen 3: Match score + gap list
│   │       ├── interview/                  # Interview flow
│   │       └── cv/                         # CV generation
│   ├── components/
│   │   ├── ui/             # Design system: Button, Card, Badge, Input, Dropzone, etc.
│   │   └── processing-overlay.tsx
│   └── lib/
│       ├── api/            # API client + error translation (errors.ts)
│       └── hooks/          # useFlow(), useFlowPolling(), useFileUpload()
├── tests/
│   └── e2e/                # Playwright E2E tests
└── docker-compose.yml
```

## Build & Run

```bash
# Start the full stack
docker compose up

# Backend only (dev)
cd backend && uvicorn apliqa.main:app --reload --port 8001

# Frontend only (dev)
cd frontend && npm run dev

# Run backend unit tests
cd backend && pytest

# Run integration tests (requires real LLM key)
INTEGRATION_LLM=1 pytest backend/tests/integration/

# Run E2E tests
npx playwright test
```

**Ports:** frontend → `3000`, backend → `8001`, postgres → `5433`

## Key Architectural Decisions

- **ADR-004 Stateful Backend:** All application state lives server-side. The frontend is a thin projection of `FlowStateResponse`. No client-side routing state.
- **ADR-008 Auth Abstraction:** Community Edition uses `NoAuthProvider` — no login screen. A stub user (`local@apliqa.community`) is created on startup.
- **ADR-002 Master Profile:** PostgreSQL JSONB, accumulation-first merge model. True conflicts (contradicting dates) stored in `metadata.pending_conflicts`.
- **ADR-001 JD Intake:** Job-first architecture. Tiered scraping: httpx → Playwright → polished fallback. No LinkedIn server-side scraping.
- **ADR-016 Flow Orchestrator:** Custom async state machine in `flow_sessions` table. Step graph drives UI navigation via `available_actions`.
- **ADR-017 Retention Worker:** Mandatory GDPR TTL enforcement — not optional.

## API Surface

| Endpoint | Purpose |
|----------|---------|
| `POST /api/flow` | Create flow session |
| `GET /api/flow/{id}/state` | Current step + available_actions |
| `POST /api/flow/{id}/advance` | Step transition |
| `POST /api/job/analyze` | JD analysis (text or URL) |
| `POST /api/profile/upload` | CV upload (multipart) |
| `POST /api/job/{id}/gaps` | Gap analysis |
| `GET /api/profile` | Master Profile |

## Brand & Design Tokens

Colors: `#1B4F72` (primary), `#2A8F9D` (teal), `#C9A84C` (gold), `#2D9F6F` (green), `#E5A832` (amber), `#D94F4F` (red)
Typography: Inter (body), Poppins (headings)
Grid: 8px base unit | Border radius: 8px / 12px

## Current Sprint

**Sprint 4 — Iteration 18:** Frontend Foundation & New User Happy Path
Sprint doc: `/home/kvmadmin/Dokumente/Apliqa/Documents/Sprints/sprint 4.md`
All implementation tasks are complete and at 🔍 Ready for Review.
