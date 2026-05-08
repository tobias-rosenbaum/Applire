# Sprint 13 — Test Infrastructure: Module System Fix & CI/CD Alignment

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unblock CI/CD E2E tests by fixing the CommonJS/ES module mismatch, squash a `require()` regression in an E2E test, align coverage threshold to 75%, and add a regression guard.

**Architecture:** The root `package.json` currently declares `"type": "commonjs"`, preventing Vitest (ES-module-only) from loading. Adding `"type": "module"` to both `package.json` files fixes resolution. One E2E test (`marcus-persona.spec.ts`) uses an inline `require('fs')` which will break in ES module mode and must be converted to a top-level static import. The CI workflow threshold (70%) has drifted from the arc42 spec (75%) and must be realigned.

**Tech Stack:** Node.js 20, Vitest 1.x, Playwright 1.58, GitHub Actions, pytest-cov

---

## File Map

| Action | File | Change |
|--------|------|--------|
| Modify | `package.json` | `"type": "commonjs"` → `"type": "module"` |
| Modify | `frontend/package.json` | add `"type": "module"` |
| Modify | `tests/e2e/marcus-persona.spec.ts` | add `import fs from 'fs'`; remove inline `require('fs')` |
| Modify | `.github/workflows/test.yml` | 70 → 75 threshold; add `module-system-check` job |
| Modify | `TESTING.md` | add ES module section; fix stale 70% references |
| Modify | `Documents/Architecture/arc42.md` | add ES module requirement note to §8.6 |

---

## Task 1: Fix root `package.json` module type

**Files:**
- Modify: `package.json:30`

- [ ] **Step 1: Make the change**

Open `package.json`. Line 30 currently reads:
```json
"type": "commonjs"
```
Change it to:
```json
"type": "module"
```

- [ ] **Step 2: Verify the file**

Run:
```bash
node -e "const p = JSON.parse(require('fs').readFileSync('package.json','utf8')); console.log(p.type)"
```
Wait — that uses `require()`, which won't work in ES module mode.  Use this instead:
```bash
python3 -c "import json,sys; d=json.load(open('package.json')); assert d['type']=='module', d['type']; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add package.json
git commit -m "fix(ci): switch root package.json to ES module mode"
```

---

## Task 2: Fix frontend `package.json` module type

**Files:**
- Modify: `frontend/package.json`

The file has no `"type"` field at all (defaults to CommonJS). Add it.

- [ ] **Step 1: Add `"type": "module"` after the `"private"` line**

The file currently starts:
```json
{
  "name": "applire-frontend",
  "version": "0.1.0",
  "private": true,
```

Change to:
```json
{
  "name": "applire-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
```

- [ ] **Step 2: Verify**

```bash
python3 -c "import json; d=json.load(open('frontend/package.json')); assert d['type']=='module'; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Smoke-test Vitest**

```bash
cd frontend && npm test
```
Expected: Vitest runs without the "cannot be imported in a CommonJS module" error. Tests may pass or fail for other reasons — that's acceptable at this step. Exit when you see the test runner output (not a module import crash).

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json
git commit -m "fix(ci): add ES module declaration to frontend package.json"
```

---

## Task 3: Fix `require('fs')` in E2E test

**Files:**
- Modify: `tests/e2e/marcus-persona.spec.ts:2` and `:177`

After switching to ES module mode, the inline `const fs = require('fs')` at line 177 will throw `ReferenceError: require is not defined`. Fix by hoisting it to a static import at the top of the file.

- [ ] **Step 1: Add `fs` import at the top of the file**

Current top of file (lines 1–2):
```typescript
import { test, expect } from '@playwright/test';
import path from 'path';
```

Change to:
```typescript
import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
```

- [ ] **Step 2: Remove the inline `require()`**

Current line 177:
```typescript
    const fs = require('fs');
```

Delete that line entirely. The `fs` identifier is now in scope from the top-level import.

- [ ] **Step 3: Verify there are no other `require()` calls in the test directory**

```bash
grep -rn "require(" tests/ --include="*.ts" --include="*.spec.ts"
```
Expected: no output (zero matches).

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/marcus-persona.spec.ts
git commit -m "fix(tests): replace require('fs') with ES module import in marcus-persona e2e test"
```

---

## Task 4: Align coverage threshold to 75% in CI/CD

**Files:**
- Modify: `.github/workflows/test.yml:42`

- [ ] **Step 1: Audit current coverage before tightening the gate**

```bash
PYTHONPATH=backend pytest tests/unit/ backend/tests/unit/ \
  --ignore=tests/conftest.py \
  --ignore=backend/tests/conftest.py \
  --cov=applire \
  --cov-config=backend/.coveragerc \
  --cov-report=term-missing \
  --cov-fail-under=75 \
  -q 2>&1 | tail -20
```

- If this **passes** → proceed to Step 2.
- If this **fails** with "FAIL Required test coverage of 75%…" → you must add tests before raising the gate. Do not change the workflow threshold until coverage is ≥75%.

> **If coverage is below 75%:** Check `--cov-report=term-missing` output for the modules with the lowest coverage. Add unit tests in `tests/unit/` to cover missing branches, then re-run until the command above passes.

- [ ] **Step 2: Update the workflow threshold**

Open `.github/workflows/test.yml`. Line 42 currently reads:
```yaml
            --cov-fail-under=70 \
```
Change to:
```yaml
            --cov-fail-under=75 \
```

- [ ] **Step 3: Verify the workflow file is valid YAML**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml')); print('YAML OK')"
```
Expected: `YAML OK`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "fix(ci): align coverage gate with arc42 spec (70% -> 75%)"
```

---

## Task 5: Add module-system-check CI job

**Files:**
- Modify: `.github/workflows/test.yml`

Add a new job that runs **before** `e2e-tests` and validates ES module mode is declared. The job must be listed as a dependency in `e2e-tests.needs`.

- [ ] **Step 1: Add the new job after the `backend-integration-tests` block**

Insert this block directly before the `e2e-tests:` job definition:

```yaml
  module-system-check:
    name: Module System Validation
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Verify ES module mode in root package.json
        run: |
          echo "Checking root package.json..."
          if ! grep -q '"type": "module"' package.json; then
            echo "❌ Root package.json must declare '\"type\": \"module\"'"
            exit 1
          fi
          echo "✅ Root package.json declares ES module mode"

      - name: Verify ES module mode in frontend package.json
        run: |
          echo "Checking frontend package.json..."
          if ! grep -q '"type": "module"' frontend/package.json; then
            echo "❌ Frontend package.json must declare '\"type\": \"module\"'"
            exit 1
          fi
          echo "✅ Frontend package.json declares ES module mode"

      - name: Check for CommonJS require() in test files
        run: |
          echo "Scanning for CommonJS require() statements in test files..."
          if grep -r "require(" tests/ frontend/ --include="*.ts" --include="*.tsx" --include="*.spec.ts" | grep -v node_modules; then
            echo "❌ Found CommonJS require() statements in test files"
            exit 1
          fi
          echo "✅ No CommonJS require() statements found"
```

- [ ] **Step 2: Add `module-system-check` to the `e2e-tests` needs list**

Current `e2e-tests` needs line:
```yaml
    needs: [backend-unit-tests, backend-integration-tests]
```
Change to:
```yaml
    needs: [backend-unit-tests, backend-integration-tests, module-system-check]
```

- [ ] **Step 3: Add `module-system-check` to `test-summary` needs**

Current `test-summary` needs line:
```yaml
    needs: [backend-unit-tests, backend-integration-tests, e2e-tests]
```
Change to:
```yaml
    needs: [backend-unit-tests, backend-integration-tests, module-system-check, e2e-tests]
```

Also update the summary generation to include the new job result. Find the `Generate test summary` step and add a row:

```yaml
          echo "| Module System Check | ${{ needs.module-system-check.result }} |" >> $GITHUB_STEP_SUMMARY
```

Insert it after the Backend Integration Tests row.

And update the failure condition:
```yaml
          if [ "${{ needs.backend-unit-tests.result }}" != "success" ] || \
             [ "${{ needs.backend-integration-tests.result }}" != "success" ] || \
             [ "${{ needs.module-system-check.result }}" != "success" ] || \
             [ "${{ needs.e2e-tests.result }}" != "success" ]; then
```

- [ ] **Step 4: Validate YAML**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml')); print('YAML OK')"
```
Expected: `YAML OK`

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "feat(ci): add module-system-check job to prevent ES module regressions"
```

---

## Task 6: Update TESTING.md

**Files:**
- Modify: `TESTING.md`

Two changes: (1) add an ES Module System section, (2) fix the stale 70% reference in the CI/CD section.

- [ ] **Step 1: Add ES Module System section**

Find the `## CI/CD Pipeline` heading. Insert the following section **before** it:

```markdown
## Module System

Applire uses **ES modules** (`"type": "module"`) for all JavaScript/TypeScript code.

- Use `import` statements — never `require()`
- Vitest and Playwright are ES module-native; they require `"type": "module"` in `package.json`
- All test files (`.spec.ts`, `.test.ts`) must use ES module syntax
- Both `package.json` (root) and `frontend/package.json` declare `"type": "module"`
- A CI/CD gate (`module-system-check` job) enforces this on every push

---

```

- [ ] **Step 2: Fix the stale 70% coverage threshold reference**

Find this line in `TESTING.md`:
```
- **Coverage Threshold**: 70%
```

Change it to:
```
- **Coverage Threshold**: 75%
```

- [ ] **Step 3: Commit**

```bash
git add TESTING.md
git commit -m "docs: update TESTING.md — ES module requirement and 75% coverage threshold"
```

---

## Task 7: Update arc42 Section 8.6

**Files:**
- Modify: `Documents/Architecture/arc42.md` (around line 1092–1094)

The section currently ends with:

```markdown
**Local Testing Mirror**:
- Developers can run the same test suite locally using `pytest` and `npx playwright test`
- Documentation in `TESTING.md` (Phase 1b/2) will detail local setup, commands, and troubleshooting
```

- [ ] **Step 1: Add ES module requirement note**

Replace that paragraph with:

```markdown
**Local Testing Mirror**:
- Developers can run the same test suite locally using `pytest` and `npx playwright test`
- See `TESTING.md` for local setup, commands, and troubleshooting

**Module System Requirement**:
- All JavaScript/TypeScript code (tests, config, frontend) uses ES modules (`"type": "module"`)
- Both `package.json` (root) and `frontend/package.json` must declare `"type": "module"`
- The `module-system-check` CI job enforces this on every push (see ADR-020)
- Never use `require()` in test files — use static `import` statements
```

- [ ] **Step 2: Commit**

```bash
git add Documents/Architecture/arc42.md
git commit -m "docs(arc42): document ES module requirement in §8.6 CI/CD Pipeline Configuration"
```

---

## Task 8: Final verification

- [ ] **Step 1: Run Playwright tests locally**

```bash
cd /path/to/Solution
cp .env.ci .env.dev
docker compose up -d --build
# Wait for services
timeout 180 bash -c 'until curl -sf http://localhost:8001/health; do sleep 2; done'
timeout 180 bash -c 'until curl -sf http://localhost:3000; do sleep 2; done'
npx playwright test
```

Expected: all 5 spec files pass, no "cannot be imported in a CommonJS module" error.

- [ ] **Step 2: Run module-system-check commands locally**

```bash
grep -q '"type": "module"' package.json && echo "✅ root OK" || echo "❌ root FAIL"
grep -q '"type": "module"' frontend/package.json && echo "✅ frontend OK" || echo "❌ frontend FAIL"
grep -r "require(" tests/ frontend/ --include="*.ts" --include="*.spec.ts" | grep -v node_modules && echo "❌ require() found" || echo "✅ no require()"
```

Expected: all three print ✅.

- [ ] **Step 3: Push and verify CI passes**

```bash
git push origin HEAD
```

Monitor GitHub Actions. All jobs — `backend-unit-tests`, `backend-integration-tests`, `module-system-check`, `e2e-tests`, `test-summary` — must show green.

---

## Self-Review: Spec Coverage Check

| Sprint task | Covered by | Notes |
|-------------|-----------|-------|
| 23.1 Fix root `package.json` | Task 1 | ✅ |
| 23.1 Fix frontend `package.json` | Task 2 | ✅ |
| 23.2 Align coverage threshold 70→75 | Task 4 | ✅ Includes pre-flight audit |
| 23.3 Verify E2E tests pass | Task 8 | ✅ |
| 23.4 Update TESTING.md | Task 6 | ✅ |
| 23.4 Update arc42 §8.6 | Task 7 | ✅ |
| 23.5 Add module-system-check CI job | Task 5 | ✅ |
| (unlisted) Fix `require('fs')` in E2E test | Task 3 | Found during analysis — would break after Task 1+2 |

> **Note on Task 3:** The sprint spec's regression check (23.5) would have caught the `require('fs')` in CI, but it must be fixed proactively so the E2E tests pass after the module system switch.
