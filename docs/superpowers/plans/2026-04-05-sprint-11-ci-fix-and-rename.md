# Sprint 11: CI Fix & Applire → Applire Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix two CI failures that block every push, then rename the project from Applire to Applire across all back- and frontend code.

**Architecture:** CI fixes are two surgical file edits. The rename is a package directory move (`git mv`) followed by bulk sed replacements across Python, TypeScript, config, and infrastructure files — no logic changes, only identifier and string updates.

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy / Next.js 15 / TypeScript / Docker Compose / GitHub Actions

---

## File Map

### CI fixes
- Modify: `backend/requirements.txt` — add `aiosqlite`
- Modify: `.github/workflows/test.yml` — add Docker startup steps to `backend-integration-tests` job

### Rename — package
- Move: `backend/applire/` → `backend/applire/` (git mv)

### Rename — Python imports (bulk sed, all at once after mv)
- Every `*.py` under `backend/`, `tests/` — `from applire.` → `from applire.`, `import applire` → `import applire`

### Rename — string literals and config (individual edits)
- Modify: `backend/applire/main.py` — `"local@applire.community"` → `"local@applire.community"`, FastAPI title
- Modify: `backend/applire/mcp/server.py` — `FastMCP("Applire")` → `FastMCP("Applire")`, docstring, `APPLIRE_BASE_URL` comment
- Modify: `backend/applire/config.py` — `applire_base_url` field → `applire_base_url`, `applire.cloud` cloud import ref
- Modify: `backend/alembic/env.py` — already covered by import sed
- Modify: `backend/alembic.ini` — postgres connection string credentials

### Rename — infrastructure
- Modify: `backend/Dockerfile` — CMD `uvicorn applire.main:app` → `uvicorn applire.main:app`
- Modify: `docker-compose.yml` — postgres credentials, uvicorn/retention/mcp commands
- Modify: `.env.ci` — `DATABASE_URL`, `APPLIRE_CORS_ORIGINS`

### Rename — frontend
- Modify: `frontend/package.json` — `"name": "applire-frontend"` → `"applire-frontend"`
- Modify: `frontend/app/layout.tsx` — page title
- Modify: `frontend/app/page.tsx` — h1 brand name
- Modify: `frontend/app/settings/page.tsx` — export filename
- Modify: `frontend/app/flow/[flowId]/layout.tsx` — brand text
- Modify: `frontend/components/dashboard/Dashboard.tsx` — h1 brand name
- Modify: `frontend/components/cv/WhatNext.tsx` — share text strings

### Rename — tests
- Modify: `tests/e2e/marcus-persona.spec.ts` — title assertion `/Applire/i` → `/Applire/i`
- All other test file changes covered by bulk Python sed pass

---

## Task 1: CI Fix — Add aiosqlite

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add aiosqlite to requirements**

  Append to `backend/requirements.txt`:
  ```
  aiosqlite==0.20.0
  ```

- [ ] **Step 2: Verify locally that unit tests collect**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution/backend
  pip install aiosqlite==0.20.0 -q
  pytest tests/unit/ --collect-only -q 2>&1 | head -20
  ```
  Expected: lines like `<Module test_cv_html_headers.py>` — no `ModuleNotFoundError`.

- [ ] **Step 3: Commit**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  git add backend/requirements.txt
  git commit -m "fix(ci): add aiosqlite for SQLite-backed unit tests"
  ```

---

## Task 2: CI Fix — Docker Startup in Integration Test Job

**Files:**
- Modify: `.github/workflows/test.yml`

- [ ] **Step 1: Insert Docker startup steps**

  In `.github/workflows/test.yml`, find the `backend-integration-tests` job. Insert these three steps **immediately before** the `Run integration tests` step (which runs pytest):

  ```yaml
      - name: Start Docker services
        run: docker compose up -d --build

      - name: Wait for backend to be ready
        run: |
          echo "Waiting for backend..."
          timeout 180 bash -c 'until curl -sf http://localhost:8001/health; do sleep 2; done'
          echo "Backend ready."

      - name: Run database migrations
        run: docker compose exec backend python -m alembic upgrade head
  ```

- [ ] **Step 2: Verify YAML is valid**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  python -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))" && echo "YAML OK"
  ```
  Expected: `YAML OK`

- [ ] **Step 3: Commit**

  ```bash
  git add .github/workflows/test.yml
  git commit -m "fix(ci): start Docker stack before integration tests run"
  ```

---

## Task 3: Rename Python Package Directory

**Files:**
- Move: `backend/applire/` → `backend/applire/`

- [ ] **Step 1: git mv the package directory**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  git mv backend/applire backend/applire
  ```

- [ ] **Step 2: Verify the move**

  ```bash
  ls backend/applire/__init__.py && echo "package present"
  git status --short | head -10
  ```
  Expected: `package present` and a list of renamed files.

- [ ] **Step 3: Commit the directory rename (before any content changes)**

  ```bash
  git add -A
  git commit -m "refactor: rename Python package applire → applire (directory only)"
  ```

---

## Task 4: Bulk Replace Python Import Paths

**Files:**
- All `*.py` under `backend/` and `tests/` (imports only — not string literals yet)

- [ ] **Step 1: Replace `from applire.` with `from applire.` everywhere**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  find backend tests -name "*.py" | xargs sed -i 's/from applire\./from applire./g'
  ```

- [ ] **Step 2: Replace `import applire.` with `import applire.`**

  ```bash
  find backend tests -name "*.py" | xargs sed -i 's/import applire\./import applire./g'
  ```

- [ ] **Step 3: Replace bare `import applire` (not followed by dot) with `import applire`**

  This covers lines like `import applire.models.user` that slip through as well as any standalone `import applire`:
  ```bash
  find backend tests -name "*.py" | xargs sed -i 's/import applire$/import applire/g'
  ```

- [ ] **Step 4: Replace patch strings like `"applire.services.*"` in test mocks**

  These appear in `unittest.mock.patch("applire.services.linkedin.PdfReader", ...)` — they must point to the new package:
  ```bash
  find backend tests -name "*.py" | xargs sed -i 's/"applire\./"applire./g'
  find backend tests -name "*.py" | xargs sed -i "s/'applire\./'applire./g"
  ```

- [ ] **Step 5: Verify no `from applire.` or `import applire.` remain**

  ```bash
  grep -rn "from applire\.\|import applire" backend/ tests/ --include="*.py"
  ```
  Expected: **no output**. If any lines appear, fix them manually.

- [ ] **Step 6: Smoke-test imports**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution/backend
  DATABASE_URL=sqlite+aiosqlite:///./test.db python -c "from applire.config import settings; print('import OK')"
  ```
  Expected: `import OK`

- [ ] **Step 7: Collect unit tests to confirm no import errors**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution/backend
  DATABASE_URL=sqlite+aiosqlite:///./test.db pytest tests/unit/ --collect-only -q 2>&1 | tail -5
  ```
  Expected: `X tests collected` with no `ModuleNotFoundError`.

- [ ] **Step 8: Commit**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  git add -A
  git commit -m "refactor: update all Python import paths applire → applire"
  ```

---

## Task 5: Update Backend String Literals and Config Keys

**Files:**
- Modify: `backend/applire/main.py`
- Modify: `backend/applire/mcp/server.py`
- Modify: `backend/applire/config.py`

- [ ] **Step 1: Update `main.py`**

  In `backend/applire/main.py`:
  - Change `"local@applire.community"` → `"local@applire.community"`
  - Change `title="Applire API"` → `title="Applire API"`

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  sed -i 's/local@applire\.community/local@applire.community/g' backend/applire/main.py
  sed -i 's/title="Applire API"/title="Applire API"/g' backend/applire/main.py
  grep -n "applire\|Applire\|APPLIRE" backend/applire/main.py
  ```
  Expected: no output (all occurrences replaced).

- [ ] **Step 2: Update `mcp/server.py`**

  ```bash
  sed -i 's/FastMCP("Applire")/FastMCP("Applire")/g' backend/applire/mcp/server.py
  sed -i 's/Applire MCP Server/Applire MCP Server/g' backend/applire/mcp/server.py
  sed -i 's/APPLIRE_BASE_URL/APPLIRE_BASE_URL/g' backend/applire/mcp/server.py
  sed -i 's/settings\.applire_base_url/settings.applire_base_url/g' backend/applire/mcp/server.py
  grep -n "applire\|Applire\|APPLIRE" backend/applire/mcp/server.py
  ```
  Expected: no output.

- [ ] **Step 3: Update `config.py` — field name and cloud import**

  In `backend/applire/config.py`, the field `applire_base_url` maps to env var `APPLIRE_BASE_URL`. Rename to `applire_base_url` (maps to `APPLIRE_BASE_URL`). Also update the cloud package import reference:

  ```bash
  sed -i 's/applire_base_url/applire_base_url/g' backend/applire/config.py
  sed -i 's/import applire\.cloud/import applire.cloud/g' backend/applire/config.py
  sed -i 's/# APPLIRE_EDITION/# APPLIRE_EDITION/g' backend/applire/config.py
  grep -n "applire\|Applire\|APPLIRE" backend/applire/config.py
  ```
  Expected: no output.

- [ ] **Step 4: Commit**

  ```bash
  git add backend/applire/main.py backend/applire/mcp/server.py backend/applire/config.py
  git commit -m "refactor: rename Applire string literals and config keys in backend"
  ```

---

## Task 6: Update Infrastructure Files

**Files:**
- Modify: `backend/Dockerfile`
- Modify: `backend/alembic.ini`
- Modify: `docker-compose.yml`
- Modify: `.env.ci`

- [ ] **Step 1: Update Dockerfile CMD**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  sed -i 's/uvicorn applire\.main:app/uvicorn applire.main:app/g' backend/Dockerfile
  grep -n "applire\|Applire\|APPLIRE" backend/Dockerfile
  ```
  Expected: no output.

- [ ] **Step 2: Update alembic.ini postgres connection string**

  The `sqlalchemy.url` in `backend/alembic.ini` uses `applire` as DB user, password, and name. Rename all three to `applire`:

  ```bash
  sed -i 's|postgresql+asyncpg://applire:applire@postgres:5432/applire|postgresql+asyncpg://applire:applire@postgres:5432/applire|g' backend/alembic.ini
  grep -n "applire\|Applire\|APPLIRE" backend/alembic.ini
  ```
  Expected: no output.

- [ ] **Step 3: Update docker-compose.yml**

  ```bash
  # Postgres credentials
  sed -i 's/POSTGRES_USER: applire/POSTGRES_USER: applire/g' docker-compose.yml
  sed -i 's/POSTGRES_PASSWORD: applire/POSTGRES_PASSWORD: applire/g' docker-compose.yml
  sed -i 's/POSTGRES_DB: applire/POSTGRES_DB: applire/g' docker-compose.yml
  sed -i 's/pg_isready -U applire/pg_isready -U applire/g' docker-compose.yml
  # Uvicorn / retention / mcp commands
  sed -i 's/uvicorn applire\.main:app/uvicorn applire.main:app/g' docker-compose.yml
  sed -i 's/python -m applire\.retention/python -m applire.retention/g' docker-compose.yml
  sed -i 's/python -m applire\.mcp/python -m applire.mcp/g' docker-compose.yml
  # Comment in docker-compose referencing applire.mcp
  sed -i 's/applire\.mcp/applire.mcp/g' docker-compose.yml
  grep -n "applire\|Applire\|APPLIRE" docker-compose.yml
  ```
  Expected: no output.

- [ ] **Step 4: Update .env.ci**

  ```bash
  sed -i 's|postgresql+asyncpg://applire:applire@postgres:5432/applire|postgresql+asyncpg://applire:applire@postgres:5432/applire|g' .env.ci
  sed -i 's/APPLIRE_CORS_ORIGINS/APPLIRE_CORS_ORIGINS/g' .env.ci
  grep -n "applire\|Applire\|APPLIRE" .env.ci
  ```
  Expected: no output.

- [ ] **Step 5: Update alembic env.py (any remaining applire references)**

  The bulk Python sed in Task 4 covered import lines. Verify nothing remains:
  ```bash
  grep -n "applire\|Applire\|APPLIRE" backend/alembic/env.py
  ```
  If any remain, fix inline; expected: no output.

- [ ] **Step 6: Commit**

  ```bash
  git add backend/Dockerfile backend/alembic.ini docker-compose.yml .env.ci
  git commit -m "refactor: update infrastructure files applire → applire"
  ```

---

## Task 7: Update Frontend

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/app/settings/page.tsx`
- Modify: `frontend/app/flow/[flowId]/layout.tsx`
- Modify: `frontend/components/dashboard/Dashboard.tsx`
- Modify: `frontend/components/cv/WhatNext.tsx`

- [ ] **Step 1: Update package.json name**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  sed -i 's/"name": "applire-frontend"/"name": "applire-frontend"/g' frontend/package.json
  grep -n "applire\|Applire\|APPLIRE" frontend/package.json
  ```
  Expected: no output.

- [ ] **Step 2: Update layout title**

  ```bash
  sed -i 's/Applire — DACH CV Tailoring/Applire — DACH CV Tailoring/g' frontend/app/layout.tsx
  grep -n "applire\|Applire\|APPLIRE" frontend/app/layout.tsx
  ```
  Expected: no output.

- [ ] **Step 3: Update page.tsx h1**

  ```bash
  sed -i 's/>Applire</>Applire</g' frontend/app/page.tsx
  grep -n "applire\|Applire\|APPLIRE" frontend/app/page.tsx
  ```
  Expected: no output.

- [ ] **Step 4: Update settings export filename**

  ```bash
  sed -i 's/applire-export\.json/applire-export.json/g' frontend/app/settings/page.tsx
  grep -n "applire\|Applire\|APPLIRE" frontend/app/settings/page.tsx
  ```
  Expected: no output.

- [ ] **Step 5: Update flow layout brand text**

  ```bash
  sed -i 's/>Applire</>Applire</g' "frontend/app/flow/[flowId]/layout.tsx"
  grep -n "applire\|Applire\|APPLIRE" "frontend/app/flow/[flowId]/layout.tsx"
  ```
  Expected: no output.

- [ ] **Step 6: Update Dashboard h1**

  ```bash
  sed -i 's/>Applire</>Applire</g' frontend/components/dashboard/Dashboard.tsx
  grep -n "applire\|Applire\|APPLIRE" frontend/components/dashboard/Dashboard.tsx
  ```
  Expected: no output.

- [ ] **Step 7: Update WhatNext share strings**

  ```bash
  sed -i 's/mit Applire optimiert/mit Applire optimiert/g' frontend/components/cv/WhatNext.tsx
  grep -n "applire\|Applire\|APPLIRE" frontend/components/cv/WhatNext.tsx
  ```
  Expected: no output.

- [ ] **Step 8: Verify no remaining frontend references**

  ```bash
  grep -ri "applire\|Applire\|APPLIRE" frontend/app/ frontend/components/ frontend/lib/ --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" 2>/dev/null
  ```
  Expected: no output.

- [ ] **Step 9: Commit**

  ```bash
  git add frontend/package.json frontend/app/layout.tsx frontend/app/page.tsx \
    frontend/app/settings/page.tsx "frontend/app/flow/[flowId]/layout.tsx" \
    frontend/components/dashboard/Dashboard.tsx frontend/components/cv/WhatNext.tsx
  git commit -m "refactor: rename Applire → Applire in all frontend files"
  ```

---

## Task 8: Update Test Files

**Files:**
- Modify: `tests/e2e/marcus-persona.spec.ts`
- Verify: all other test files already updated by Task 4 bulk sed

- [ ] **Step 1: Update E2E title assertion**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  sed -i 's|/Applire/i|/Applire/i|g' tests/e2e/marcus-persona.spec.ts
  grep -n "applire\|Applire\|APPLIRE" tests/e2e/marcus-persona.spec.ts
  ```
  Expected: no output.

- [ ] **Step 2: Verify no remaining applire references in any test file**

  ```bash
  grep -rn "applire\|Applire\|APPLIRE" tests/ backend/tests/ --include="*.py" --include="*.ts" --include="*.spec.ts" 2>/dev/null
  ```
  Expected: no output. Fix any remaining occurrences manually.

- [ ] **Step 3: Run unit test collection to confirm all imports resolve**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution/backend
  DATABASE_URL=sqlite+aiosqlite:///./test.db pytest tests/unit/ --collect-only -q 2>&1 | tail -5
  ```
  Expected: `X tests collected, no errors`.

- [ ] **Step 4: Run unit tests**

  ```bash
  DATABASE_URL=sqlite+aiosqlite:///./test.db pytest tests/unit/ -v --tb=short 2>&1 | tail -20
  ```
  Expected: all tests pass (or same failures as before the rename — no new failures introduced).

- [ ] **Step 5: Commit**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  git add tests/e2e/marcus-persona.spec.ts
  git commit -m "refactor: update test title assertion applire → applire"
  ```

---

## Task 9: Final Verification

- [ ] **Step 1: Global zero-occurrence check**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  grep -ri "applire\|Applire\|APPLIRE" backend/ frontend/ tests/ \
    --include="*.py" --include="*.ts" --include="*.tsx" \
    --include="*.json" --include="*.yml" --include="*.ini" \
    --include="*.env*" --exclude-dir=node_modules --exclude-dir=__pycache__ \
    2>/dev/null
  ```
  Expected: **no output**. Every line that appears is a remaining issue to fix.

- [ ] **Step 2: Check root config files**

  ```bash
  grep -i "applire" .env.ci docker-compose.yml .github/workflows/test.yml backend/Dockerfile backend/alembic.ini 2>/dev/null
  ```
  Expected: no output.

- [ ] **Step 3: Verify backend starts (dry-run)**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution/backend
  DATABASE_URL=sqlite+aiosqlite:///./test.db python -c "
  import applire.main
  print('backend module loads OK')
  "
  ```
  Expected: `backend module loads OK`

- [ ] **Step 4: Validate CI YAML**

  ```bash
  cd /home/applire/Documents/applire/Applire/Solution
  python -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml')); print('YAML OK')"
  ```
  Expected: `YAML OK`

- [ ] **Step 5: Final commit summary**

  If any loose files were missed, stage and commit them now:
  ```bash
  git status --short
  # If anything remains uncommitted:
  git add -A
  git commit -m "refactor: final cleanup of remaining applire → applire references"
  ```
