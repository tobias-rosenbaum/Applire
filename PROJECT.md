# Project Knowledge
Apliqa is a open core SAAS solution centered around helping people to successfully apply to new jobs. In it's first iteration, it is a tool focused on quickly creating tailored CVs for a given job description using a master profile of the applicant.

## Tech Stack
React, Next.js, FastAPI, Docker, TypeScript

## Architecture
Apliqa is a unknown project with 192 files (19.923 lines of code). Tech stack: React, Next.js, FastAPI, Docker, TypeScript. Contains 141 classes and 2712 functions across 3 language(s).
Detaild description of the architecture can be found in the architecture subfolder.

## Key Files & Directories
**Entry Points:**
- `Solution/backend/apliqa/main.py`
- `Solution/backend/apliqa/mcp/server.py`

**Key Files:**
- `Solution/frontend/app/flow/[flowId]/cv/page.tsx` — Complex module with extensive API
- `Solution/frontend/app/flow/[flowId]/gaps/page.tsx` — Complex module with extensive API
- `Solution/backend/apliqa/services/cv_parser.py` — Complex module with extensive API
- `Solution/frontend/app/flow/[flowId]/import/page.tsx` — Complex module with extensive API
- `Solution/tests/test_iter8_jd_url_intake.py` — URL routing
- `Solution/backend/alembic/versions/0013_iter17_foundation.py` — Complex module with extensive API
- `Solution/backend/apliqa/providers/llm/openai.py` — Complex module with extensive API
- `Solution/backend/apliqa/services/gap.py` — Complex module with extensive API
- `Solution/backend/apliqa/services/linkedin.py` — Complex module with extensive API
- `Solution/backend/apliqa/providers/llm/openrouter.py` — URL routing
- `Solution/backend/apliqa/providers/llm/ollama.py` — Complex module with extensive API
- `Solution/tests/unit/test_iter7_mcp_resources.py` — Test suite
- `Solution/backend/apliqa/routers/application.py` — Complex module with extensive API
- `Solution/tests/test_iter3_gap_analysis.py` — Test suite
- `Solution/backend/apliqa/models/application.py` — Core module with multiple classes

**Key Directories**
- `/Documents` - all project related documentation needs to be stored within this folder structure. Documents should be organized by area of responsibility (e.g. Architect, Product Owner...)
- `/Solution` - the actual project that is connected to the github repository

## Build & Run Commands
```bash
npm run dev     # Start Next.js dev server
npm run build   # Production build
npm test        # Run tests
```
```bash
pip install -r requirements.txt   # Install deps
python app.py                     # Start server
```

## Conventions
_Conventions will be learned as the AI works with this project._

## Dependencies
next, react, react-dom, fastapi, uvicorn[standard], pydantic, pydantic-settings, sqlalchemy[asyncio], asyncpg, alembic, mistralai, openai, httpx, python-dotenv, pymupdf, python-docx, pypdf, python-multipart

## Testing Strategy & CI/CD
## Testing Strategy (Three-Tier, Feature-Gated)

**Tier 1: Pre-Commit (Local)** - Unit tests, type checking, linting (advisory)
**Tier 2: Post-Commit/CI** - Backend unit tests (≥75% coverage, blocking), integration tests (Docker), E2E tests Playwright (blocking)
**Tier 3: Pre-Rollout** - Manual QA against acceptance criteria, feature flag verification

**CI/CD Pipeline:** `.github/workflows/test.yml` runs on every push/PR to main/develop. Stages: backend unit → integration → E2E. 15-20 min timeout. Artifacts: coverage reports, Playwright reports, screenshots.

**E2E Testing:** Playwright tests in `Solution/tests/e2e/`. Initial scope: Marcus persona happy path (CV upload → JD input → Processing → Results → Download). Runs on GitHub Actions runner, connects to containerized backend at localhost:3000.

**Test Data:** Committed to Git in `Solution/tests/fixtures/` for reproducibility. Includes sample JD and CV instructions. Developers can add custom fixtures (all committed).

**LLM Mocking:** CI/CD mocks all LLM providers (Mistral, OpenAI, Ollama, OpenRouter). Real APIs used only for quality measurement (separate from blocking tests).

**Configuration:** `Solution/playwright.config.ts` optimized for both local development and CI. 60-second timeout per test, 1 worker (serial), retries: 2 on CI, 0 locally.

**Documentation:** Section 8 added to `/Documents/Architecture/arc42.md` with full testing strategy. Phase 1b/2 will add `TESTING.md` with local setup instructions and release checklist.

## Business Plan
- Current version: **v2.0** (2026-03-27) at `Documents/Business Strategy/20260327_businessplan_v2.md`
- Previous version: v1.0 (2026-03-24) at `Documents/Business Strategy/20260324_075027_businessplan.md`
- Key v2.0 changes: Broadened market positioning (all DACH applicants, not just regulated industries), added Product Vision section with Mock Interviews, Gamification, Career Development, Job Search features

## GitHub Configuration
- **GitHub Username:** tobias-rosenbaum
- **Repository SSH URL:** git@github.com:tobias-rosenbaum/Apliqa.git
- **Repository HTTPS URL:** https://github.com/tobias-rosenbaum/Apliqa.git
- **Authentication Method:** SSH (enabled and configured)

## Repository Structure
The Apliqa repository has a nested directory structure critical for CI/CD and development:

```
Apliqa/                                    ← Repository root (GitHub repo)
├── .github/
│   └── workflows/
│       └── test.yml                       ← CI/CD workflow (executes from repo root)
├── Solution/                              ← Primary project folder (git-tracked)
│   ├── backend/
│   │   ├── requirements.txt
│   │   └── apliqa/
│   ├── frontend/
│   │   ├── package.json
│   │   ├── package-lock.json
│   │   └── app/
│   ├── tests/
│   ├── docker-compose.yml
│   └── Solution/                          ← Nested Solution folder (purpose unclear)
├── Documents/                             ← Local workspace folder (NOT git-tracked)
└── [other repo files]
```

**Critical Notes for CI/CD & Development:**
- All relative paths in workflows and scripts must prefix with `Solution/` (e.g., `Solution/backend/requirements.txt`, `Solution/frontend/package.json`)
- `docker-compose.yml` is at `Solution/docker-compose.yml`
- `Documents/` is a local-only workspace folder, not part of version control
- GitHub Actions run from repo root (`Apliqa/`), so path prefixing is essential
